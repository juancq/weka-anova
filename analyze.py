import argparse
import numpy as np
import arff
from collections import defaultdict
import scipy.stats as stats
from itertools import combinations
from tabulate import tabulate
import traceback
import nemenyi

def main():
    '''
    Performs anova on Weka experimenter results arff file.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="file containing acc data")
    parser.add_argument("-o", "--output_file", type=str, help="output file", default = None)
    parser.add_argument("-f", help="remove commas from Key_Dataset attribute, otherwise arff parsing fails", action='store_true')
    parser.add_argument("-v", help="verbose", action='store_true')
    args = parser.parse_args()

    arff_file = args.input_file
    verbose = args.v
    output_file = args.output_file
    clean = args.f


    # the key_dataset field may have commas inside quotes, which breaks
    # the arff parsing. Force removing of commas.
    data_str = open(arff_file, 'rb').read()
    if clean: 
        data_split = data_str.split('\n')
        for line in data_split:
            index = line.find('Key_Dataset')
            if index > -1:
                start = line.find('{')
                end = line.find('}')
                dataset_str = line[start+1:end-1]
                # remove whitespace and '' if surrounding the value
                dataset_str = dataset_str.strip().strip("'")
                break
                
        dataset_str_clean = dataset_str.replace(',', '')
        data_str = data_str.replace(dataset_str, dataset_str_clean)

    try: 
        arff_data = arff.load(data_str)
    except:
        print '*' * 20
        traceback.print_exc()
        print '*' * 20
        print 'POSSIBLE SOLUTION: try running with -f' 
        print 'analyze.py input_file -f'
        print '*' * 20
        return

    attributes = arff_data['attributes']
    data = arff_data['data']

    print '-' * 10
    print 'Attributes:'
    print 'Select one or more (i.e. 1, 2, 8)'
    for i, v in enumerate(attributes):
        print '{}. {}'.format(i + 1, v[0])
    
    selected_attributes = raw_input('> ')
    selected_attributes = map(lambda x: int(x) - 1, selected_attributes.strip().split(','))
    print 'selected: '
    for attr in selected_attributes:
        print '\t- {}'.format(attributes[attr][0])

    print '-' * 10
    pc_index = -1
    classifier_index = -1
    done = 0
    for i, v in enumerate(attributes):
        if v[0] == 'Percent_correct':
            pc_index = i
            done += 1
        elif v[0] == 'Key_Scheme':
            classifier_index = i
            done += 1
        if done >= 2:
            break

    results = defaultdict(list)

    for record in data:
        key = record[classifier_index]
        value = record[pc_index]
        results[key].append(value)

    clean_names = [name.split('.')[-1] for name in results.keys()]
    width = max([len(name) for name in clean_names])
    for i, (name, result) in enumerate(results.iteritems()):
        name = clean_names[i]
        mean = np.mean(result)
        std = np.std(result)
        print '{:<{width}} : {:>6.2f} ({:>6.3f})'.format(name, mean, std, width=width)
        #print '%s: %.2f (%.3f)' % (clean_name, mean, std)

    anova = stats.f_oneway(*results.values())
    print 'anova', anova

    stat_results = nemenyi.kw_nemenyi(results.values())
    print stat_results

    p_corrected = stat_results[2]
    reject = stat_results[-1]

    print 'results'

    to_compare = tuple(combinations(range(len(results)), 2))
    ncomp = len(to_compare)

    table = []
    labels = ['A', 'B', 'p-value', 'reject']
    table.append(labels)
    for pp, (ii, jj) in enumerate(to_compare):
        name_ii = clean_names[ii]
        name_jj = clean_names[jj]
        #table.append(print '{:>{width}}-{:>{width}}: p-value {:.3f} {}'.format(
        table.append([name_ii, name_jj, 
                    '%.3f' % p_corrected[pp], reject[pp]])

    print tabulate(table, tablefmt='grid')

    if output_file:
        np.savetxt(output_file, table, delimiter=',', fmt='%s')

if __name__ == "__main__":
    main()


