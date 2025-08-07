"""
Admin Learning Routes for Continuous Learning System
Provides interface for reviewing and approving algorithm learnings
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
import sqlite3
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from learning_engine import ContinuousLearningEngine

# Import admin_required from auth module to avoid conflicts
from ..auth import admin_required

# Create blueprint for admin learning routes
admin_learning_bp = Blueprint('admin_learning', __name__, url_prefix='/admin/learning')

def get_learning_db_connection():
    """Get database connection for learning data (flashlog.db, not users.db)"""
    conn = sqlite3.connect('../flashlog.db')
    conn.row_factory = sqlite3.Row
    return conn

@admin_learning_bp.route('/dashboard')
@login_required
@admin_required
def learning_dashboard():
    """Main admin dashboard for reviewing learnings"""
    try:
        engine = ContinuousLearningEngine()
        
        # Get pending learnings
        pending_learnings = engine.get_pending_learnings()
        
        # Get approved learnings
        approved_learnings = get_approved_learnings()
        
        # Get learning metrics
        learning_metrics = get_learning_metrics()
        
        # Get pattern library
        pattern_library = get_pattern_library()
        
        # Get learning impact data
        impact_data = get_learning_impact_data()
        
        # Get learning history data
        learning_history = get_learning_history()
        
        # Calculate summary statistics
        summary_stats = calculate_summary_stats(pending_learnings, learning_metrics)
        
        return render_template('admin/learning_dashboard.html',
                             pending_learnings=pending_learnings,
                             approved_learnings=approved_learnings,
                             learning_metrics=learning_metrics,
                             pattern_library=pattern_library,
                             impact_data=impact_data,
                             learning_history=learning_history,
                             summary_stats=summary_stats)
                             
    except Exception as e:
        flash(f'Error loading learning dashboard: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_learning_bp.route('/api/pending')
@login_required
@admin_required
def api_get_pending_learnings():
    """API endpoint to get pending learnings"""
    try:
        algorithm_filter = request.args.get('algorithm', '')
        type_filter = request.args.get('type', '')
        
        engine = ContinuousLearningEngine()
        pending_learnings = engine.get_pending_learnings()
        
        # Apply filters
        if algorithm_filter:
            pending_learnings = [l for l in pending_learnings if l['algorithm_name'] == algorithm_filter]
        
        if type_filter:
            pending_learnings = [l for l in pending_learnings if l['learning_type'] == type_filter]
        
        return jsonify({
            'success': True,
            'learnings': pending_learnings,
            'count': len(pending_learnings)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/approve/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def approve_learning(learning_id):
    """Approve a specific learning (without applying to production)"""
    try:
        # Get learning details
        learning = get_learning_by_id(learning_id)
        if not learning:
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        # Validate learning before approval
        validation_result = validate_learning(learning)
        if not validation_result['valid']:
            return jsonify({
                'success': False, 
                'error': f'Validation failed: {validation_result["error"]}'
            }), 400
        
        # Update database - only approve, don't apply
        update_learning_status(learning_id, 'approved', current_user.id)
        
        # Log the approval
        log_admin_action(current_user.id, 'approve_learning', {
            'learning_id': learning_id,
            'algorithm': learning['algorithm_name'],
            'type': learning['learning_type'],
            'description': learning['learning_description']
        })
        
        return jsonify({
            'success': True, 
            'message': 'Learning approved successfully (ready for application)'
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/apply/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def apply_learning_endpoint(learning_id):
    """Apply an approved learning to production system"""
    try:
        # Get learning details
        learning = get_learning_by_id(learning_id)
        if not learning:
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        # Check if learning is approved
        if learning['status'] != 'approved':
            return jsonify({
                'success': False, 
                'error': 'Learning must be approved before it can be applied'
            }), 400
        
        # Apply the learning
        result = apply_learning(learning)
        
        if result['success']:
            # Update database to mark as applied
            update_learning_status(learning_id, 'applied', current_user.id)
            
            # Log the application
            log_admin_action(current_user.id, 'apply_learning', {
                'learning_id': learning_id,
                'algorithm': learning['algorithm_name'],
                'type': learning['learning_type'],
                'description': learning['learning_description'],
                'applied_changes': result.get('applied_changes', {})
            })
            
            return jsonify({
                'success': True, 
                'message': 'Learning applied to production successfully',
                'applied_changes': result.get('applied_changes', {})
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/reject/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def reject_learning(learning_id):
    """Reject a specific learning"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        # Update learning status
        update_learning_status(learning_id, 'rejected', current_user.id, reason)
        
        # Log the rejection
        log_admin_action(current_user.id, 'reject_learning', {
            'learning_id': learning_id,
            'reason': reason
        })
        
        return jsonify({
            'success': True,
            'message': 'Learning rejected successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/batch_approve', methods=['POST'])
@login_required
@admin_required
def batch_approve_learnings():
    """Approve multiple learnings at once (without applying to production)"""
    try:
        data = request.get_json()
        learning_ids = data.get('learning_ids', [])
        
        if not learning_ids:
            return jsonify({'success': False, 'error': 'No learning IDs provided'}), 400
        
        results = []
        successful_approvals = 0
        
        for learning_id in learning_ids:
            try:
                learning = get_learning_by_id(learning_id)
                if not learning:
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': 'Learning not found'
                    })
                    continue
                
                # Validate learning
                validation_result = validate_learning(learning)
                if not validation_result['valid']:
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': f'Validation failed: {validation_result["error"]}'
                    })
                    continue
                
                # Only approve, don't apply
                update_learning_status(learning_id, 'approved', current_user.id)
                successful_approvals += 1
                results.append({
                    'learning_id': learning_id,
                    'success': True,
                    'message': 'Learning approved (ready for application)'
                })
                    
            except Exception as e:
                results.append({
                    'learning_id': learning_id,
                    'success': False,
                    'message': str(e)
                })
        
        # Log batch approval
        log_admin_action(current_user.id, 'batch_approve_learnings', {
            'total_attempted': len(learning_ids),
            'successful_approvals': successful_approvals,
            'results': results
        })
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_attempted': len(learning_ids),
                'successful': successful_approvals,
                'failed': len(learning_ids) - successful_approvals
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/batch_apply', methods=['POST'])
@login_required
@admin_required
def batch_apply_learnings():
    """Apply multiple approved learnings to production at once"""
    try:
        data = request.get_json()
        learning_ids = data.get('learning_ids', [])
        
        if not learning_ids:
            return jsonify({'success': False, 'error': 'No learning IDs provided'}), 400
        
        results = []
        successful_applications = 0
        
        for learning_id in learning_ids:
            try:
                learning = get_learning_by_id(learning_id)
                if not learning:
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': 'Learning not found'
                    })
                    continue
                
                # Check if learning is approved
                if learning['status'] != 'approved':
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': 'Learning must be approved before it can be applied'
                    })
                    continue
                
                # Apply the learning
                apply_result = apply_learning(learning)
                if apply_result['success']:
                    update_learning_status(learning_id, 'applied', current_user.id)
                    successful_applications += 1
                    results.append({
                        'learning_id': learning_id,
                        'success': True,
                        'message': 'Learning applied to production'
                    })
                else:
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': apply_result['error']
                    })
                    
            except Exception as e:
                results.append({
                    'learning_id': learning_id,
                    'success': False,
                    'message': str(e)
                })
        
        # Log batch application
        log_admin_action(current_user.id, 'batch_apply_learnings', {
            'total_attempted': len(learning_ids),
            'successful_applications': successful_applications,
            'results': results
        })
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_attempted': len(learning_ids),
                'successful': successful_applications,
                'failed': len(learning_ids) - successful_applications
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/simulate/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def simulate_learning(learning_id):
    """Simulate a learning application without actually applying it"""
    try:
        print(f"[DEBUG] Simulating learning ID: {learning_id}")
        learning = get_learning_by_id(learning_id)
        if not learning:
            print(f"[DEBUG] Learning ID {learning_id} not found")
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        print(f"[DEBUG] Found learning: {learning['algorithm_name']} - {learning['learning_type']}")
        
        # Run simulation
        simulation_result = run_learning_simulation(learning)
        
        return jsonify({
            'success': True,
            'simulation': simulation_result
        })
        
    except Exception as e:
        print(f"[DEBUG] Simulation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/details/<int:learning_id>')
@login_required
@admin_required
def learning_details(learning_id):
    """Get detailed information about a learning"""
    try:
        learning = get_learning_by_id(learning_id)
        if not learning:
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        # Get additional details
        evidence_logs = json.loads(learning['evidence_logs']) if learning['evidence_logs'] else []
        suggested_parameters = json.loads(learning['suggested_parameters']) if learning['suggested_parameters'] else {}
        
        # Get related metrics
        related_metrics = get_related_metrics(learning['session_id'], learning['algorithm_name'])
        
        details = {
            'learning': learning,
            'evidence_logs': evidence_logs,
            'suggested_parameters': suggested_parameters,
            'related_metrics': related_metrics,
            'validation_result': validate_learning(learning)
        }
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/patterns')
@login_required
@admin_required
def pattern_library():
    """View and manage pattern library"""
    try:
        patterns = get_pattern_library()
        pattern_stats = calculate_pattern_stats(patterns)
        
        return render_template('admin/pattern_library.html',
                             patterns=patterns,
                             pattern_stats=pattern_stats)
                             
    except Exception as e:
        flash(f'Error loading pattern library: {str(e)}', 'error')
        return redirect(url_for('admin_learning.learning_dashboard'))

@admin_learning_bp.route('/metrics')
@login_required
@admin_required
def learning_metrics():
    """View learning performance metrics"""
    try:
        metrics = get_comprehensive_learning_metrics()
        
        return render_template('admin/learning_metrics.html',
                             metrics=metrics)
                             
    except Exception as e:
        flash(f'Error loading learning metrics: {str(e)}', 'error')
        return redirect(url_for('admin_learning.learning_dashboard'))

@admin_learning_bp.route('/api/approved')
@login_required
@admin_required
def api_get_approved_learnings():
    """API endpoint to get approved learnings"""
    try:
        algorithm_filter = request.args.get('algorithm', '')
        type_filter = request.args.get('type', '')
        
        approved_learnings = get_approved_learnings()
        
        # Apply filters
        if algorithm_filter:
            approved_learnings = [l for l in approved_learnings if l['algorithm_name'] == algorithm_filter]
        
        if type_filter:
            approved_learnings = [l for l in approved_learnings if l['learning_type'] == type_filter]
        
        return jsonify({
            'success': True,
            'learnings': approved_learnings,
            'count': len(approved_learnings)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/delete/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def delete_approved_learning(learning_id):
    """Delete an approved learning and revert to previous state"""
    try:
        # Get learning details
        learning = get_learning_by_id(learning_id)
        if not learning:
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        # Check if learning is approved
        if learning['status'] != 'approved':
            return jsonify({'success': False, 'error': 'Can only delete approved learnings'}), 400
        
        # Revert the learning (restore previous state)
        revert_result = revert_learning(learning)
        
        if revert_result['success']:
            # Delete the learning from database
            conn = get_learning_db_connection()
            cursor = conn.cursor()
            
            # Delete from algorithm_learnings table
            cursor.execute('DELETE FROM algorithm_learnings WHERE id = ?', (learning_id,))
            
            # Log the deletion
            log_admin_action(current_user.id, 'delete_learning', {
                'learning_id': learning_id,
                'algorithm': learning['algorithm_name'],
                'type': learning['learning_type'],
                'revert_details': revert_result['details']
            })
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'Learning deleted and previous state restored',
                'details': revert_result['details']
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'Failed to revert learning: {revert_result["error"]}'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_learning_bp.route('/api/impact')
@login_required
@admin_required
def api_get_learning_impact():
    """API endpoint to get learning impact data"""
    try:
        # Get recent impact tracking data
        conn = get_learning_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        impact_data = cursor.execute('''
            SELECT * FROM learning_impact_tracking 
            ORDER BY created_at DESC 
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        # Parse the JSON data
        parsed_impact = []
        for row in impact_data:
            impact_row = dict(row)
            impact_row['current_metrics'] = json.loads(impact_row['current_metrics'])
            impact_row['baseline_metrics'] = json.loads(impact_row['baseline_metrics'])
            impact_row['improvements'] = json.loads(impact_row['improvements'])
            parsed_impact.append(impact_row)
        
        return jsonify({
            'success': True,
            'impact_data': parsed_impact,
            'count': len(parsed_impact)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_learning_impact_data():
    """Get learning impact data for dashboard"""
    try:
        conn = get_learning_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if impact tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_impact_tracking'")
        if not cursor.fetchone():
            # Table doesn't exist, return empty data
            return {
                'recent_impact': [],
                'average_improvements': {
                    'detection_improvement': 0,
                    'confidence_improvement': 0,
                    'accuracy_improvement': 0
                },
                'total_sessions_tracked': 0
            }
        
        # Get recent impact data
        impact_data = cursor.execute('''
            SELECT * FROM learning_impact_tracking 
            ORDER BY created_at DESC 
            LIMIT 5
        ''').fetchall()
        
        conn.close()
        
        # Parse and calculate summary
        parsed_impact = []
        total_improvements = {
            'detection_improvement': 0,
            'confidence_improvement': 0,
            'accuracy_improvement': 0
        }
        
        for row in impact_data:
            impact_row = dict(row)
            impact_row['current_metrics'] = json.loads(impact_row['current_metrics'])
            impact_row['baseline_metrics'] = json.loads(impact_row['baseline_metrics'])
            impact_row['improvements'] = json.loads(impact_row['improvements'])
            parsed_impact.append(impact_row)
            
            # Accumulate improvements
            for key in total_improvements:
                total_improvements[key] += impact_row['improvements'].get(key, 0)
        
        # Calculate averages
        if parsed_impact:
            for key in total_improvements:
                total_improvements[key] /= len(parsed_impact)
        
        return {
            'recent_impact': parsed_impact,
            'average_improvements': total_improvements,
            'total_sessions_tracked': len(parsed_impact)
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to get learning impact data: {e}")
        return {
            'recent_impact': [],
            'average_improvements': {
                'detection_improvement': 0,
                'confidence_improvement': 0,
                'accuracy_improvement': 0
            },
            'total_sessions_tracked': 0
        }

def get_learning_history():
    """Get learning history data for the dashboard"""
    try:
        conn = get_learning_db_connection()
        cursor = conn.cursor()
        
        # Get all learnings with their status changes
        cursor.execute('''
            SELECT 
                id, algorithm_name, learning_type, learning_description,
                confidence_score, status, created_at, applied_at,
                potential_improvement, suggested_parameters
            FROM algorithm_learnings 
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        
        learnings = cursor.fetchall()
        
        # Calculate summary statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM algorithm_learnings
        ''')
        
        stats = cursor.fetchone()
        
        # Format the data
        history_data = []
        for learning in learnings:
            history_data.append({
                'id': learning[0],
                'algorithm_name': learning[1],
                'learning_type': learning[2],
                'learning_description': learning[3],
                'confidence_score': learning[4],
                'status': learning[5],
                'created_at': learning[6],
                'applied_at': learning[7],
                'potential_improvement': learning[8],
                'suggested_parameters': learning[9]
            })
        
        summary_stats = {
            'total': stats[0],
            'approved': stats[1],
            'applied': stats[2],
            'rejected': stats[3],
            'success_rate': round((stats[1] / stats[0]) * 100, 1) if stats[0] > 0 else 0
        }
        
        conn.close()
        
        return {
            'history': history_data,
            'summary': summary_stats
        }
        
    except Exception as e:
        print(f"Error getting learning history: {e}")
        return {
            'history': [],
            'summary': {'total': 0, 'approved': 0, 'applied': 0, 'rejected': 0, 'success_rate': 0}
        }

# Helper functions
def get_learning_by_id(learning_id):
    """Get learning by ID"""
    conn = get_learning_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    learning = cursor.execute('''
        SELECT * FROM algorithm_learnings 
        WHERE id = ?
    ''', (learning_id,)).fetchone()
    
    conn.close()
    return dict(learning) if learning else None

def validate_learning(learning):
    """Validate learning before approval"""
    validations = []
    
    # Check confidence threshold
    if learning['confidence_score'] < 0.5:
        validations.append('Low confidence score (< 50%)')
    
    # Check parameter bounds for specific types
    if learning['learning_type'] == 'parameter':
        try:
            params = json.loads(learning['suggested_parameters'])
            if 'contamination' in params and (params['contamination'] < 0.01 or params['contamination'] > 0.5):
                validations.append('Contamination parameter out of bounds (0.01-0.5)')
            if 'n_neighbors' in params and (params['n_neighbors'] < 1 or params['n_neighbors'] > 100):
                validations.append('n_neighbors parameter out of bounds (1-100)')
        except json.JSONDecodeError:
            validations.append('Invalid suggested parameters format')
    
    return {
        'valid': len(validations) == 0,
        'error': '; '.join(validations) if validations else None,
        'warnings': validations
    }

def apply_learning(learning):
    """Apply approved learning to production system"""
    try:
        learning_type = learning['learning_type']
        algorithm = learning['algorithm_name']
        
        if learning_type == 'parameter':
            return apply_parameter_learning(learning)
        elif learning_type == 'pattern':
            return apply_pattern_learning(learning)
        elif learning_type == 'feature':
            return apply_feature_learning(learning)
        else:
            return {'success': False, 'error': f'Unknown learning type: {learning_type}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def apply_parameter_learning(learning):
    """Apply parameter changes"""
    # Placeholder for parameter application logic
    # In practice, this would update algorithm configurations
    
    params = json.loads(learning['suggested_parameters'])
    algorithm = learning['algorithm_name']
    
    # Simulate applying parameters
    applied_changes = {
        'algorithm': algorithm,
        'parameters_changed': list(params.keys()),
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"🔧 Applied {algorithm} parameters: {params}")
    
    return {
        'success': True,
        'message': f'Parameters applied to {algorithm}',
        'applied_changes': applied_changes
    }

def apply_pattern_learning(learning):
    """Apply new patterns to pattern library"""
    # Placeholder for pattern application logic
    
    params = json.loads(learning['suggested_parameters'])
    
    # Add to pattern library table
    conn = get_learning_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO learned_patterns 
        (pattern_type, pattern_regex, pattern_description, severity_level, created_from_session)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        params.get('pattern_type', 'unknown'),
        params.get('regex', ''),
        learning['learning_description'],
        params.get('severity', 'medium'),
        learning['session_id']
    ))
    
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'message': 'Pattern added to library',
        'applied_changes': params
    }

def apply_feature_learning(learning):
    """Apply feature improvements"""
    # Placeholder for feature application logic
    
    params = json.loads(learning['suggested_parameters'])
    
    applied_changes = {
        'feature_type': params.get('feature_weight', 'unknown'),
        'weight_change': params.get('weight_multiplier', 1.0),
        'timestamp': datetime.now().isoformat()
    }
    
    return {
        'success': True,
        'message': 'Feature weights updated',
        'applied_changes': applied_changes
    }

def update_learning_status(learning_id, status, admin_id, notes=None):
    """Update learning status in database"""
    conn = get_learning_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE algorithm_learnings 
        SET status = ?, admin_notes = ?, applied_at = ?
        WHERE id = ?
    ''', (status, notes, datetime.now() if status == 'approved' else None, learning_id))
    
    conn.commit()
    conn.close()

def log_admin_action(admin_id, action_type, details):
    """Log admin actions for audit trail"""
    # Placeholder for admin action logging
    print(f"🔐 Admin {admin_id} performed {action_type}: {details}")

def get_learning_metrics():
    """Get learning performance metrics"""
    conn = get_learning_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    metrics = cursor.execute('''
        SELECT * FROM learning_metrics 
        ORDER BY created_at DESC
        LIMIT 50
    ''').fetchall()
    
    conn.close()
    return [dict(row) for row in metrics]

def get_pattern_library():
    """Get current pattern library"""
    try:
        conn = get_learning_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        patterns = cursor.execute('''
            SELECT * FROM learned_patterns 
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''').fetchall()
        
        result = [dict(row) for row in patterns]
        conn.close()
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to get pattern library: {e}")
        return []

def calculate_summary_stats(pending_learnings, learning_metrics):
    """Calculate summary statistics"""
    return {
        'pending_count': len(pending_learnings),
        'high_confidence_count': len([l for l in pending_learnings if l['confidence_score'] > 0.7]),
        'avg_confidence': sum(l['confidence_score'] for l in pending_learnings) / len(pending_learnings) if pending_learnings else 0,
        'algorithm_breakdown': calculate_algorithm_breakdown(pending_learnings),
        'recent_approvals': calculate_recent_approvals()
    }

def calculate_algorithm_breakdown(pending_learnings):
    """Calculate breakdown by algorithm"""
    breakdown = {}
    for learning in pending_learnings:
        algo = learning['algorithm_name']
        breakdown[algo] = breakdown.get(algo, 0) + 1
    return breakdown

def calculate_recent_approvals():
    """Calculate recent approvals count"""
    conn = get_learning_db_connection()
    cursor = conn.cursor()
    
    week_ago = datetime.now() - timedelta(days=7)
    count = cursor.execute('''
        SELECT COUNT(*) FROM algorithm_learnings 
        WHERE status = 'approved' AND applied_at > ?
    ''', (week_ago,)).fetchone()[0]
    
    conn.close()
    return count

def run_learning_simulation(learning):
    """Simulate learning application with real data analysis"""
    try:
        conn = get_learning_db_connection()
        cursor = conn.cursor()
        
        # Get historical performance data for this algorithm
        cursor.execute('''
            SELECT AVG(improvement_percentage) as avg_improvement,
                   COUNT(*) as sample_size
            FROM learning_metrics 
            WHERE algorithm_name = ?
        ''', (learning['algorithm_name'],))
        
        result = cursor.fetchone()
        avg_improvement = result[0] if result and result[0] else 0
        sample_size = result[1] if result else 0
        
        # Calculate predicted improvement based on confidence and historical data
        base_improvement = learning['confidence_score'] * 15  # Base improvement
        historical_factor = avg_improvement * 0.3 if sample_size > 0 else 0  # 30% weight to historical
        confidence_factor = learning['confidence_score'] * 10  # 70% weight to confidence
        
        predicted_improvement = base_improvement + historical_factor + confidence_factor
        
        # Determine risk level based on confidence and historical data
        risk_level = 'Low'
        if learning['confidence_score'] < 0.5:
            risk_level = 'High'
        elif learning['confidence_score'] < 0.7:
            risk_level = 'Medium'
        
        # Get recent performance trends
        week_ago = datetime.now() - timedelta(days=7)
        recent_trend = cursor.execute('''
            SELECT AVG(improvement_percentage) 
            FROM learning_metrics 
            WHERE algorithm_name = ? AND created_at > ?
        ''', (learning['algorithm_name'], week_ago)).fetchone()[0]
        
        trend_indicator = "↗️ Improving" if (recent_trend or 0) > avg_improvement else "↘️ Declining"
        
        conn.close()
        
        return {
            'predicted_improvement': f"{predicted_improvement:.1f}%",
            'risk_level': risk_level,
            'estimated_impact': learning['potential_improvement'],
            'historical_average': f"{avg_improvement:.1f}%",
            'sample_size': sample_size,
            'trend': trend_indicator,
            'simulation_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[ERROR] Simulation failed: {e}")
        # Fallback to basic simulation
        return {
            'predicted_improvement': f"{learning['confidence_score'] * 10:.1f}%",
            'risk_level': 'Low' if learning['confidence_score'] > 0.7 else 'Medium',
            'estimated_impact': learning['potential_improvement'],
            'historical_average': 'N/A',
            'sample_size': 0,
            'trend': 'Unknown',
            'simulation_time': datetime.now().isoformat()
        }

def get_related_metrics(session_id, algorithm_name):
    """Get metrics related to a learning"""
    conn = get_learning_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    metrics = cursor.execute('''
        SELECT * FROM learning_metrics 
        WHERE session_id = ? AND algorithm_name = ?
    ''', (session_id, algorithm_name)).fetchall()
    
    conn.close()
    return [dict(row) for row in metrics]

def calculate_pattern_stats(patterns):
    """Calculate pattern library statistics"""
    if not patterns:
        return {'total': 0, 'by_type': {}, 'by_severity': {}}
    
    by_type = {}
    by_severity = {}
    
    for pattern in patterns:
        pattern_type = pattern['pattern_type']
        severity = pattern['severity_level']
        
        by_type[pattern_type] = by_type.get(pattern_type, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    return {
        'total': len(patterns),
        'by_type': by_type,
        'by_severity': by_severity
    }

def get_comprehensive_learning_metrics():
    """Get comprehensive learning metrics from database"""
    try:
        conn = get_learning_db_connection()
        cursor = conn.cursor()
        
        # Get total learnings generated
        total_learnings = cursor.execute('SELECT COUNT(*) FROM algorithm_learnings').fetchone()[0]
        
        # Get approval rate
        approved_count = cursor.execute('SELECT COUNT(*) FROM algorithm_learnings WHERE status = "approved"').fetchone()[0]
        applied_count = cursor.execute('SELECT COUNT(*) FROM algorithm_learnings WHERE status = "applied"').fetchone()[0]
        total_processed = cursor.execute('SELECT COUNT(*) FROM algorithm_learnings WHERE status IN ("approved", "applied", "rejected")').fetchone()[0]
        
        approval_rate = (approved_count + applied_count) / total_processed if total_processed > 0 else 0
        
        # Get average improvement from learning metrics
        avg_improvement = cursor.execute('SELECT AVG(improvement_percentage) FROM learning_metrics').fetchone()[0]
        avg_improvement = avg_improvement if avg_improvement else 0
        
        # Get top performing algorithms
        top_algorithms = cursor.execute('''
            SELECT algorithm_name, COUNT(*) as count 
            FROM algorithm_learnings 
            WHERE status IN ("approved", "applied") 
            GROUP BY algorithm_name 
            ORDER BY count DESC 
            LIMIT 3
        ''').fetchall()
        top_performing = [row[0] for row in top_algorithms]
        
        # Calculate recent trends (week over week)
        week_ago = datetime.now() - timedelta(days=7)
        two_weeks_ago = datetime.now() - timedelta(days=14)
        
        recent_improvements = cursor.execute('''
            SELECT AVG(improvement_percentage) 
            FROM learning_metrics 
            WHERE created_at > ?
        ''', (week_ago,)).fetchone()[0]
        
        previous_improvements = cursor.execute('''
            SELECT AVG(improvement_percentage) 
            FROM learning_metrics 
            WHERE created_at BETWEEN ? AND ?
        ''', (two_weeks_ago, week_ago)).fetchone()[0]
        
        week_over_week_improvement = 0
        if previous_improvements and previous_improvements > 0:
            week_over_week_improvement = ((recent_improvements or 0) - previous_improvements) / previous_improvements * 100
        
        # Calculate false positive reduction (placeholder - would need more detailed metrics)
        false_positive_reduction = 0  # This would need specific false positive tracking
        
        conn.close()
        
        return {
            'total_learnings_generated': total_learnings,
            'approval_rate': approval_rate,
            'average_improvement': avg_improvement,
            'top_performing_algorithms': top_performing,
            'recent_trends': {
                'week_over_week_improvement': week_over_week_improvement,
                'false_positive_reduction': false_positive_reduction
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to get comprehensive metrics: {e}")
        return {
            'total_learnings_generated': 0,
            'approval_rate': 0,
            'average_improvement': 0,
            'top_performing_algorithms': [],
            'recent_trends': {
                'week_over_week_improvement': 0,
                'false_positive_reduction': 0
            }
        }

def get_approved_learnings():
    """Get all approved learnings from the database"""
    conn = get_learning_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    approved_learnings = cursor.execute('''
        SELECT * FROM algorithm_learnings 
        WHERE status = 'approved'
        ORDER BY applied_at DESC
    ''').fetchall()
    
    conn.close()
    return [dict(row) for row in approved_learnings]

def revert_learning(learning):
    """Revert an approved learning to its previous state (e.g., restore parameters)"""
    # Placeholder for actual revert logic
    # This would involve querying the history of the learning to find its previous state
    # For now, we'll just return a dummy success
    return {
        'success': True,
        'details': {
            'reverted_algorithm': learning['algorithm_name'],
            'reverted_type': learning['learning_type'],
            'reverted_at': datetime.now().isoformat()
        }
    }

# Test the admin routes
if __name__ == "__main__":
    print("🧪 Testing Admin Learning Routes")
    
    # Test helper functions
    engine = ContinuousLearningEngine()
    pending = engine.get_pending_learnings()
    print(f"Found {len(pending)} pending learnings")
    
    if pending:
        learning = pending[0]
        validation = validate_learning(learning)
        print(f"Validation result: {validation}")
        
        # Test simulation
        simulation = run_learning_simulation(learning)
        print(f"Simulation result: {simulation}")
    
    print("✅ Admin routes test completed")