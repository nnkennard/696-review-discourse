from scipy.stats import pearsonr, spearmanr

import argparse
import collections
import json

parser = argparse.ArgumentParser(
    description='Find features that are significantly correlated with an annotation field')

parser.add_argument('-a',
                    '--adjudicated_annotation_file',
                    type=str,
                    help='path to adjudicated annotation file')

parser.add_argument('-d',
                    '--run_directory',
                    type=str,
                    help='path to run directory that contains final features file')

parser.add_argument('-c',
                    '--correlation_field',
                    type=str,
                    help='field in the annotation file to correlate features with')

corr_function = pearsonr


def get_correlation(feature_values, annotation_field_values):
  correlation, p_value = corr_function(feature_values, annotation_field_values)
  return {'correlation': correlation, 'p-value': p_value}


def get_all_feature_names(features_file):
  with open(features_file, 'r') as f:
    final_features = json.load(f)
  for review_id, features in final_features.items():
    return features.keys()


def get_feature_values(annotation_file, features_file, correlation_field):
  all_feature_names = get_all_feature_names(features_file)
  feature_values = {feature_name: [] for feature_name in all_feature_names}
  feature_values['score'] = []

  with open(annotation_file, 'r') as f:
    final_annotations = json.load(f)
  
  with open(features_file, 'r') as f:
    final_features = json.load(f)
  
  for review in final_annotations:
    review_id = review['review_id']
    features = final_features.get(review_id)
    if features and review['gold_annotation']:
      for feature_name in all_feature_names:
        feature_values[feature_name].append(features.get(feature_name, 0))
      feature_values['score'].append(review['gold_annotation'].get(correlation_field))

  return feature_values


def main():

  args = parser.parse_args()
  features_file = args.run_directory + "/final_features.json"
  output_file = args.run_directory + "/correlations.json"

  feature_values = get_feature_values(
    args.adjudicated_annotation_file, 
    features_file, 
    args.correlation_field
  )
  feature_correlations = collections.defaultdict(dict)

  for feature_name in get_all_feature_names(features_file):
    feature_correlations[feature_name] = get_correlation(feature_values[feature_name], feature_values['score'])

  with open(output_file, 'w') as f:
    json.dump(feature_correlations, f)


if __name__ == "__main__":
  main()