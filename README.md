#Dataset Generator

This repository contains the code for a simple dataset generator writen in Python 3. 
The code was created to help reproduce a synthetic dataset similar to the one used for the Situation-Aware Fear Learning model tests in the paper 'A Situation-Aware Fear Learning (SAFEL) model for robots' by Rizzi Raymundo, Caroline & Johnson, Colin & Fabris, Fabio & Vargas, Patricia. (2016) Neurocomputing. 221 pages 32-47. DOI: [https://doi.org/10.1016/j.neucom.2016.09.035]

May expand to more general functionality later

##Usage

`python3 generateDataset.py`

Currently only a single python file *generateDataset.py* that expects a *situations.json* and a *situationSequence.json* file to be present and generates 10 instances of the sequence the Situation Sequence file describes where each each situation is describe in the Situations file. 

Example files are provided. They were used to generate a dataset for testing a python reimplementation of part of SAFEL with some modifications. Available in https://github.com/fjpavm/SAEL
