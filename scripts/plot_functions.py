import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def bar_plot_emissions(emissions_summary, function='sum'):
    """This function creates a bar plot for summarising the emissions table"""
    colors_rice = ['forestgreen', 'seagreen', 'saddlebrown', 'peru', 'darkslategrey', 'maroon', 'darkorange']

    if emissions_summary.shape[0] == 1:
        cdata = emissions_summary.drop(['id_event', 'municipality'], axis=1).copy()
        height = cdata.iloc[0].values
        bars = cdata.iloc[0].index.values

    else:
        cdata = emissions_summary.drop(['id_event', 'municipality'], axis=1).copy()
        if function == 'mean':
            cdata = cdata.mean(axis=0)
        else:
            cdata = cdata.sum(axis=0)
        height = cdata.values
        bars = cdata.index.values

    y_pos = np.arange(len(bars))

    plt.barh(y_pos, height, color=colors_rice)
    plt.yticks(y_pos, bars)
    plt.title(r'GHG emissions (kg CO$_2$ eq $ha^{-1}$)')
    plt.show()


def polyfit_smooth(x, y, degree=5, x_seq_seqlength=100):
    val_withoutnan = np.array(x)[np.logical_not(np.isnan(x))]
    x_smooth = np.linspace(val_withoutnan.min(), val_withoutnan.max(), x_seq_seqlength)
    y_toplot = np.array(y)[np.logical_not(np.isnan(y))]
    x_toplot = np.array(x)[np.logical_not(np.isnan(y))]

    x_toplot2 = np.array(x_toplot)[np.logical_not(np.isnan(x_toplot))]
    y_toplot2 = np.array(y_toplot)[np.logical_not(np.isnan(x_toplot))]

    coefs = np.polyfit(x_toplot2, y_toplot2, degree)

    return [x_smooth, np.polyval(coefs, x_smooth)]

def yield_emissions_comparison_plot(ghg_df, remove_zeros=True):
    datatoplot = pd.DataFrame({'n_amount': ghg_df._N_total_amount,
                               'cropyield': ghg_df._yield,
                               'fertiliser induced emissions': ghg_df.emissions_summary[
                                   'Fertlises induced field emissions'].values})
    # Create some mock data

    if remove_zeros:
        datatoplot = datatoplot.loc[datatoplot['n_amount'] > 0]

    fig, ax1 = plt.subplots()
    x_smooth, y_smooth = polyfit_smooth(datatoplot.n_amount, datatoplot.cropyield)
    color = 'tab:red'
    ax1.set_xlabel('Nitrogen (kg/ha)')
    ax1.set_ylabel('Yield (kg/ha)', color=color)
    ax1.plot(x_smooth, y_smooth, color=color)
    ax1.scatter(datatoplot.n_amount, datatoplot.cropyield, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel(r'Fertiliser induced emissions\n' + '(kg CO$_2$ eq $ha^{-1}$)',
                   color=color)  # we already handled the x-label with ax1
    ax2.scatter(datatoplot.n_amount, datatoplot['fertiliser induced emissions'], color=color)
    x_smooth, y_smooth = polyfit_smooth(datatoplot.n_amount, datatoplot['fertiliser induced emissions'])
    ax2.plot(x_smooth, y_smooth, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()