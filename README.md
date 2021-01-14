# Greenhouse gas (GHG) emissions for agriculture
<p align="center">
<img src="https://ciat.cgiar.org/wp-content/uploads/Alliance_logo.png" alt="CIAT" id="logo" data-height-percentage="90" data-actual-width="140" data-actual-height="55">
<img src="images/CCAFS.png" alt="CCAFS" id="logo2" data-height-percentage="90" width="230" height="52">
</p>


## 1. Introducción

The GHG measurement, produced by agricultural activities such as fertilizers, irrigation, tillage, among others, is important for quantifying the impact that this sector has on climate change. For that reason, several methodologies have been proposed to address a baseline measurement using data from farmers. The main purpose of this repository is to offer a tool able to gauge GHG emissions estimation for multiple commercial cropping events. It is important to mention that this work is based on the Mitigation Option Tool for Agriculture project([CCAFS - MOT](https://ccafs.cgiar.org/research/projects/mitigation-options-tool-agriculture-ccafs-mot)) developed by CCAFS and The Aberdeen University.


## Requirements

* Python Version >= 3.6
* Libraries:
```txt
    pandas==1.1.0
    rasterio==1.1.8
    matplotlib==3.3.2
    numpy==1.19.1
```
## Get started

The following example shows how to use this code for ghg emissions 

###  Organice your Input

The inputs file must contain certain amount of parameters for each crop event(please check the example locateds in data folder).
There are two files, which one reffers to general information about the crop event, and second one provides insights about the fertilizers used furing the crop cicle.

The general information that are required for running the code are:

* id_event: Which is an unique idetification for the crop event.
* longitude and latitude: these are the field spatial coordinates 
* climate: 
* crop: crop that was planted.
* crop_yield_kg_ha: crop productivity

The fertiliser file must have the following variables:

* id_event: Which is an unique idetification for the crop event.
* fertliser_product: fertilizer that was used during the crop cicle.
* amount_kg_ha: how many kg/ha of fertliser was added to the soil.

Aditional variables are expleained in each excel file.

Once both files are filled with the required inputs, you can start with the code.

```python
from scripts import crop_ghg_emissions as ghg

ghg_data = ghg.ghg_emissions('data/inputs_mot_example.xlsx', ## file path to the general information 
                             'data/fertiliser_inputs_mot_example.xlsx', ## file path to the fertilizers information   
                             id_event= 'event_7' ## you can ppoint out an specif crop event, or for run through the all events don't put this paremeter)
```
### Visualization

A bar blot is used to show the CO<sub>2</sub> eq . ha<sup>-1</sup> for each emission sources. 

```python
plot_functions.bar_plot_emissions(
    ghg_data.emissions_summary, #  table summary obtained from previous step
    'mean' # function to aggregated all crop events)

```
<p align="center">
<img src="images/output1.png" alt="barplot" id="logo" width="400" height="200">
</p>

### Data downloading

Finally, you can download the summary table, which is a pandas dataframe type. Only one parameter must be provided which is the file output path.

```python
ghg_data.emissions_summary.to_csv("example.csv")
```


