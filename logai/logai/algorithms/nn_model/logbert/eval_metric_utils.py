
from sklearn import metrics
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import logging

def __plot_roc(x, y, label, y_name, x_name, fig_name):
    
    plt.plot(x, y, label=label)
    plt.ylabel(y_name)
    plt.xlabel(x_name)
    plt.legend(loc=4)
    plt.savefig(fig_name)

    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

def __plot_scores_kde(scores_pos, scores_neg, fig_name):
    
    plt.rcParams["figure.figsize"] = [7.00, 3.50]
    plt.rcParams["figure.autolayout"] = True

    fig1 = plt.figure()
    sns.kdeplot(scores_pos, bw=0.5, color="blue")

    fig2 = plt.figure()
    sns.kdeplot(scores_neg, bw=0.5, color="red")

    pp = PdfPages(fig_name)
    fig_nums = plt.get_fignums()
    figs = [plt.figure(n) for n in fig_nums]
    for fig in figs:
        fig.savefig(pp, format="pdf")
    pp.close()

    fig1.clear()
    fig2.clear()
    plt.close(fig1)
    plt.close(fig2)
    plt.cla()

def compute_metrics(eval_metrics_per_instance_series, test_labels, test_counts=None):
    
    eval_metrics_per_instance_series["indices"] = eval_metrics_per_instance_series[
        "indices"
    ].astype(int)
    y = []
    loss_mean = []
    loss_max = []
    loss_top6_mean = []
    scores_top6_max_prob = []
    scores_top6_min_logprob = []
    scores_top6_max_entropy = []
    for data in eval_metrics_per_instance_series.groupby("indices"):
        index = int(data[0])
        if index not in test_labels:
            raise Exception("Cannot find index in test ", index)
        max_losses = np.array(list(data[1]["max_loss"]))
        sum_losses = sum(list(data[1]["sum_loss"]))
        num_losses = sum(list(data[1]["num_loss"]))
        top6_losses_mean = np.mean(
            np.array(
                sorted(np.array(data[1]["top6_loss"]).flatten().tolist(), reverse=True)[
                    :6
                ]
            )
        )
        top6_max_prob = np.mean(
            1.0
            - np.array(
                sorted(np.array(data[1]["top6_max_prob"]).flatten().tolist())[:6]
            )
        )
        top6_min_logprob = np.mean(
            np.array(
                sorted(
                    np.array(data[1]["top6_min_logprob"]).flatten().tolist(),
                    reverse=True,
                )[:6]
            )
        )
        top6_max_entropy = np.mean(
            np.array(
                sorted(
                    np.array(data[1]["top6_max_entropy"]).flatten().tolist(),
                    reverse=True,
                )[:6]
            )
        )
        label = test_labels[index]
        if test_counts is not None:
            count = test_counts[index]
            y.extend([label] * count)
            if num_losses == 0:
                loss_mean.extend([0.0] * count)
            else:
                loss_mean.extend([sum_losses / num_losses] * count)
            loss_max.extend([np.max(max_losses)] * count)
            loss_top6_mean.extend([top6_losses_mean] * count)
            scores_top6_max_prob.extend([top6_max_prob] * count)
            scores_top6_min_logprob.extend([top6_min_logprob] * count)
            scores_top6_max_entropy.extend([top6_max_entropy] * count)
        else:
            y.append(label)
            if num_losses == 0:
                loss_mean.append(0.0)
            else:
                loss_mean.append(sum_losses / num_losses)
            loss_max.append(np.max(max_losses))
            loss_top6_mean.append(top6_losses_mean)
            scores_top6_max_prob.append(top6_max_prob)
            scores_top6_min_logprob.append(top6_min_logprob)
            scores_top6_max_entropy.append(top6_max_entropy)

    __compute_auc_roc(
        y,
        loss_mean,
        loss_max,
        loss_top6_mean,
        scores_top6_max_prob,
        scores_top6_min_logprob,
        scores_top6_max_entropy,
    )

    return

def __compute_auc_roc(
    y,
    loss_mean,
    loss_max,
    loss_top6_mean,
    scores_top6_max_prob,
    scores_top6_min_logprob,
    scores_top6_max_entropy,
    plot_graph=False,
    plot_histogram=False,
):
    
    __compute_auc_roc_for_metric(
        y=y,
        metric=loss_mean,
        metric_name_str="loss_mean",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )
    __compute_auc_roc_for_metric(
        y=y,
        metric=loss_max,
        metric_name_str="loss_max",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )
    __compute_auc_roc_for_metric(
        y=y,
        metric=loss_top6_mean,
        metric_name_str="loss_top6_mean",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )
    __compute_auc_roc_for_metric(
        y=y,
        metric=scores_top6_max_prob,
        metric_name_str="scores_top6_max_prob",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )
    __compute_auc_roc_for_metric(
        y=y,
        metric=scores_top6_min_logprob,
        metric_name_str="scores_top6_min_logprob",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )
    __compute_auc_roc_for_metric(
        y=y,
        metric=scores_top6_max_entropy,
        metric_name_str="scores_top6_max_entropy",
        plot_graph=plot_graph,
        plot_histogram=plot_histogram,
    )

def __compute_auc_roc_for_metric(
    y, metric, metric_name_str, plot_graph=False, plot_histogram=False
):
    
    metric_pos = np.array([metric[i] for i in range(len(metric)) if y[i] == 1])
    metric_neg = np.array([metric[i] for i in range(len(metric)) if y[i] == 0])

    if metric_pos.shape[0] > 0:
        logging.info(
            "{} Pos scores:  mean: {}, std: {}".format(
                metric_name_str, np.mean(metric_pos), np.std(metric_pos)
            )
        )
    if metric_neg.shape[0] > 0:
        logging.info(
            "{} Neg scores: mean: {}, std: {}".format(
                metric_name_str, np.mean(metric_neg), np.std(metric_neg)
            )
        )

    try:
        fpr_mean, tpr_mean, thresholds = metrics.roc_curve(y, metric, pos_label=1)
        auc_mean = metrics.roc_auc_score(y, metric)
        logging.info("AUC of {}: {}".format(metric_name_str, auc_mean))

    except:
        pass

    logging.info("\n")

    if plot_graph:
        __plot_roc(
            fpr_mean,
            tpr_mean,
            "AUC=" + str(auc_mean),
            "tpr_mean",
            "fpr_mean",
            metric_name_str + "_auc.png",
        )
    if plot_histogram:
        __plot_scores_kde(metric_pos, metric_neg, metric_name_str + "_hist.pdf")
