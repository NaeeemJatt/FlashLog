"""
Admin Learning Routes for Continuous Learning System
Provides interface for reviewing and approving algorithm learnings
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
import sqlite3
import json
from datetime import datetime, timedelta
from learning_engine import ContinuousLearningEngine

# Create blueprint for admin learning routes
admin_learning_bp = Blueprint('admin_learning', __name__, url_prefix='/admin/learning')

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('auth.auth_page'))
        return f(*args, **kwargs)
    return decorated_function

@admin_learning_bp.route('/dashboard')
@login_required
@admin_required
def learning_dashboard():
    """Main admin dashboard for reviewing learnings"""
    try:
        engine = ContinuousLearningEngine()
        
        # Get pending learnings
        pending_learnings = engine.get_pending_learnings()
        
        # Get learning metrics
        learning_metrics = get_learning_metrics()
        
        # Get pattern library
        pattern_library = get_pattern_library()
        
        # Calculate summary statistics
        summary_stats = calculate_summary_stats(pending_learnings, learning_metrics)
        
        return render_template('admin/learning_dashboard.html',
                             pending_learnings=pending_learnings,
                             learning_metrics=learning_metrics,
                             pattern_library=pattern_library,
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
    """Approve a specific learning"""
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
        
        # Apply the learning
        result = apply_learning(learning)
        
        if result['success']:
            # Update database
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
                'message': 'Learning approved and applied successfully',
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
    """Approve multiple learnings at once"""
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
                
                # Validate and apply learning
                validation_result = validate_learning(learning)
                if not validation_result['valid']:
                    results.append({
                        'learning_id': learning_id,
                        'success': False,
                        'message': f'Validation failed: {validation_result["error"]}'
                    })
                    continue
                
                apply_result = apply_learning(learning)
                if apply_result['success']:
                    update_learning_status(learning_id, 'approved', current_user.id)
                    successful_approvals += 1
                    results.append({
                        'learning_id': learning_id,
                        'success': True,
                        'message': 'Learning approved and applied'
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

@admin_learning_bp.route('/simulate/<int:learning_id>', methods=['POST'])
@login_required
@admin_required
def simulate_learning(learning_id):
    """Simulate a learning application without actually applying it"""
    try:
        learning = get_learning_by_id(learning_id)
        if not learning:
            return jsonify({'success': False, 'error': 'Learning not found'}), 404
        
        # Run simulation
        simulation_result = run_learning_simulation(learning)
        
        return jsonify({
            'success': True,
            'simulation': simulation_result
        })
        
    except Exception as e:
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

# Helper functions
def get_learning_by_id(learning_id):
    """Get learning by ID"""
    conn = sqlite3.connect('flashlog.db')
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
    conn = sqlite3.connect('flashlog.db')
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
    conn = sqlite3.connect('flashlog.db')
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
    conn = sqlite3.connect('flashlog.db')
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
    conn = sqlite3.connect('flashlog.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    patterns = cursor.execute('''
        SELECT * FROM learned_patterns 
        WHERE status = 'active'
        ORDER BY created_at DESC
    ''').fetchall()
    
    conn.close()
    return [dict(row) for row in patterns]

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
    conn = sqlite3.connect('flashlog.db')
    cursor = conn.cursor()
    
    week_ago = datetime.now() - timedelta(days=7)
    count = cursor.execute('''
        SELECT COUNT(*) FROM algorithm_learnings 
        WHERE status = 'approved' AND applied_at > ?
    ''', (week_ago,)).fetchone()[0]
    
    conn.close()
    return count

def run_learning_simulation(learning):
    """Simulate learning application"""
    # Placeholder for simulation logic
    return {
        'predicted_improvement': f"{learning['confidence_score'] * 10:.1f}%",
        'risk_level': 'Low' if learning['confidence_score'] > 0.7 else 'Medium',
        'estimated_impact': learning['potential_improvement'],
        'simulation_time': datetime.now().isoformat()
    }

def get_related_metrics(session_id, algorithm_name):
    """Get metrics related to a learning"""
    conn = sqlite3.connect('flashlog.db')
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
    """Get comprehensive learning metrics"""
    # Placeholder for comprehensive metrics
    return {
        'total_learnings_generated': 150,
        'approval_rate': 0.68,
        'average_improvement': 12.5,
        'top_performing_algorithms': ['lof', 'isolation_forest'],
        'recent_trends': {
            'week_over_week_improvement': 5.2,
            'false_positive_reduction': 15.3
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