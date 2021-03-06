## SecuML
## Copyright (C) 2016-2017  ANSSI
##
## SecuML is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## SecuML is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with SecuML. If not, see <http://www.gnu.org/licenses/>.

## package for float division (/)
## in order to perform integer division (//)
from __future__ import division
import json
import matplotlib.pyplot as plt
import pandas as pd

from LabelsStats import LabelsStats
from SecuML.Tools import colors_tools
from SecuML.Tools import dir_tools

def getEstimatorColor(e):
    color = 'blue'
    if e == 'errors':
        color = 'red'
    elif e == 'annotations':
        color = 'purple'
    return color

class LabelsMonitoring(object):

    def __init__(self, monitoring):
        self.monitoring = monitoring
        self.has_true_labels = self.monitoring.datasets.instances.hasTrueLabels()

    def generateMonitoring(self):
        self.labeled_monitoring = LabelsStats()
        self.labeled_monitoring.loadStats(self)
        self.unlabeled_monitoring = LabelsStats()
        self.unlabeled_monitoring.loadStats(self, unlabeled = True)
        self.families_monitoring = self.generateFamiliesMonitoring()

    def exportMonitoring(self):
        monitoring_dir, evolution_dir = self.getOutputDirectories()
        evolution_file = evolution_dir + 'labels_monitoring.csv'
        self.jsonExport(monitoring_dir + 'labels_monitoring.json')
        self.displayCsvLine(evolution_file)
        self.plotEvolutionMonitoring(evolution_file, monitoring_dir)

    def getOutputDirectories(self):
        monitoring_dir = self.monitoring.iteration_dir + 'labels_monitoring/'
        dir_tools.createDirectory(monitoring_dir)

        evolution_dir  = self.monitoring.al_dir + 'labels_monitoring/'
        if self.monitoring.iteration_number == 1:
            dir_tools.createDirectory(evolution_dir)

        return monitoring_dir, evolution_dir


    #############################
    #############################
    ##### Private functions #####
    #############################
    #############################

    def generateFamiliesMonitoring(self):
        instances = self.monitoring.datasets.instances
        monitoring = {}
        for l in ['malicious', 'benign']:
            monitoring[l] = len(instances.getFamiliesValues(label = l))
        monitoring['global'] = monitoring['malicious'] + monitoring['benign']
        return monitoring

    def jsonExport(self, monitoring_file):
        labels = {}
        labels['unlabeled']   = self.unlabeled_monitoring.stats['global'].labels
        labels['annotations'] = self.labeled_monitoring.stats['global'].annotations
        labels['families']   = self.families_monitoring
        with open(monitoring_file, 'w') as f:
            json.dump(labels, f, indent = 2)

    def generateLabelMonitoring(self, label, unlabeled = False):
        datasets = self.monitoring.datasets
        if unlabeled:
            instances = datasets.getUnlabeledInstances()
            monitoring = self.unlabeled_monitoring
        else:
            instances = datasets.getLabeledInstances()
            monitoring = self.labeled_monitoring
        label_stats = monitoring.stats[label]
        label_stats.labels = instances.numInstances(
                label = label, true_labels = False)
        if unlabeled:
            label_stats.annotations = 0
        else:
            label_stats.annotations = datasets.num_annotations[label]
        label_stats.errors = instances.numLabelingErrors(label = label)






    def displayCsvLine(self, evolution_file):
        if self.monitoring.iteration_number == 1:
            self.displayCsvHeader(evolution_file)
        with open(evolution_file, 'a') as f:
            v = []
            v.append(self.monitoring.iteration_number)
            v += self.labeled_monitoring.vectorRepresentation()
            for l in ['malicious', 'benign', 'global']:
                v.append(self.families_monitoring[l])
            print >>f, ','.join(map(str, v))

    def displayCsvHeader(self, evolution_file):
        with open(evolution_file, 'w') as f:
            header  = ['iteration']
            header += self.labeled_monitoring.vectorHeader()
            for l in ['malicious', 'benign', 'global']:
                header.append('families_' + l)
            print >>f, ','.join(header)


    def loadEvolutionMonitoring(self, evolution_file):
        with open(evolution_file, 'r') as f:
            data = pd.read_csv(f, header = 0, index_col = 0)
        self.evolutions = {}
        for l in ['global', 'malicious', 'benign']:
            self.evolutions[l] = {}
            for e in ['annotations', 'labels', 'errors', 'families']:
                self.evolutions[l][e] = list(data.loc[:][e + '_' + l])
            ## Automatic labels
            self.evolutions[l]['auto_labels'] = [x - y for x, y in zip(
                self.evolutions[l]['labels'], self.evolutions[l]['annotations'])]

    def plotEvolutionMonitoring(self, evolution_file, iteration_dir):
        self.loadEvolutionMonitoring(evolution_file)
        self.plotLabelsEvolutionMonitoring(iteration_dir)
        self.plotFamiliesEvolutionMonitoring(iteration_dir)

    def plotLabelsEvolutionMonitoring(self, iteration_dir):
        ## x = Iterations
        ## y = Annotations, Labels, Errors
        iterations = range(self.monitoring.iteration_number)
        for l in ['malicious', 'benign', 'global']:
            plt.clf()
            max_value = self.labeled_monitoring.stats[l].getMaxValue()
            if self.has_true_labels:
                estimators = ['labels', 'errors', 'annotations']
            else:
                estimators = ['labels', 'annotations']
            for e in estimators:
                color = getEstimatorColor(e)
                plt.plot(iterations, self.evolutions[l][e],
                        label = e,
                        color = color, linewidth = 4, marker = 'o')
            plt.ylim(0, self.computeYmax(l, max_value))
            plt.xlabel('Iteration')
            plt.ylabel('Num Instances')
            lgd = plt.legend(bbox_to_anchor = (0., 1.02, 1., .102), loc = 3,
                    ncol = 2, mode = 'expand', borderaxespad = 0.,
                    fontsize = 'x-large')
            filename  = iteration_dir
            filename += 'iteration_' + l + '.png'
            plt.savefig(filename, bbox_extra_artists=(lgd,), bbox_inches = 'tight')
            plt.clf()
        plt.clf()
        ## x = Annotations
        ## y = Labels
        plt.plot(self.evolutions['global']['annotations'],
                self.evolutions['global']['labels'],
                label = 'blue',
                color = color, linewidth = 4, marker = 'o')
        max_value = self.labeled_monitoring.stats['global'].getMaxValue()
        plt.ylim(0, self.computeYmax(l, max_value))
        plt.xlabel('Annotations')
        plt.ylabel('Labels')
        filename  = iteration_dir
        filename += 'annotations_labels_' + 'global' + '.png'
        plt.savefig(filename)
        ## x = Annotations
        ## y = Labels / NumInstances
        num_instances = self.monitoring.datasets.numInstances()
        plt.plot(self.evolutions['global']['annotations'],
                [x / num_instances for x in self.evolutions['global']['labels']],
                label = 'blue',
                color = color, linewidth = 4, marker = 'o')
        max_value = self.labeled_monitoring.stats['global'].getMaxValue()
        plt.ylim(0, 1)
        plt.xlabel('Annotations')
        plt.ylabel('Proportion of labeled instances')
        filename  = iteration_dir
        filename += 'annotations_prop_labels_' + 'global' + '.png'
        plt.savefig(filename)

    def plotFamiliesEvolutionMonitoring(self, iteration_dir):
        annotations = self.evolutions['global']['annotations']
        plt.clf()
        if self.has_true_labels:
            max_value = 1
        else:
            max_value = max(self.families_monitoring['malicious'],
                    self.families_monitoring['benign'])
        for l in ['malicious', 'benign']:
            evolution = self.evolutions[l]['families']
            if self.has_true_labels:
                num_families = len(self.monitoring.datasets.instances.getFamiliesValues(
                    label = l, true_labels = True))
                evolution = [x / num_families for x in evolution]
            color = colors_tools.getLabelColor(l)
            plt.plot(annotations, evolution,
                    label = l.title(),
                    color = color, linewidth = 4, marker = 'o')
        plt.ylim(0, max_value)
        plt.xlabel('Num Annotations')
        if self.has_true_labels:
            plt.ylabel('Prop. Families Discovered')
        else:
            plt.ylabel('Num. Families Discovered')
        lgd = plt.legend(bbox_to_anchor = (0., 1.02, 1., .102), loc = 3,
                ncol = 2, mode = 'expand', borderaxespad = 0.,
                fontsize = 'x-large')
        filename  = iteration_dir
        filename += 'families_monitoring.png'
        plt.savefig(filename, bbox_extra_artists=(lgd,), bbox_inches='tight')
        plt.clf()

    def computeYmax(self, label, max_value):
        datasets = self.monitoring.datasets
        if label in ['malicious', 'benign']:
            if self.has_true_labels:
                ymax = datasets.numInstances(label, true_labels = True)
            else:
                ymax = 0
        else:
            ymax = datasets.numInstances()
        ymax = max(ymax, max_value)
        return ymax
