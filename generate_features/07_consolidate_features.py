"""Consolidate features generated by different models."""

import argparse
import collections
import json
import numpy as np

import pipeline_lib

parser = argparse.ArgumentParser(
    description='Consolidate annotations into single file')
parser.add_argument(
    '-d',
    '--run_directory',
    type=str,
    help='JSON file with review text to annotate with specificity')


def count_key(arg_name):
  return "count_{0}".format(arg_name)


def normalized_key(arg_name):
  return "norm_{0}".format(arg_name)


def featurize_list(feature_list):
  transformed = {}
  feat_counter = collections.Counter(feature_list)
  for arg_name, count in feat_counter.items():
    transformed[count_key(arg_name)] = count
    transformed[normalized_key(arg_name)] = count / len(feature_list)
  return transformed


def transform_argument(features):
  return featurize_list(features["argument_labels"])


def transform_aspect(features):
  feature_names = [aspect.split('_')[0] for aspect, span in features["aspect_spans"]]
  for i in range(len(feature_names)):
      if feature_names[i] == 'meaningful':
          feature_names[i] = 'comparison'

  aspect_features = featurize_list(feature_names)
  aspect_features['aspect_coverage'] = len(set(feature_names)) / 8
  return aspect_features


def central_tendencies(values, name):
  return {
      "mean_{0}".format(name): np.mean(values),
      "min_{0}".format(name): min(values),
      "max_{0}".format(name): max(values),
      "median_{0}".format(name): np.median(values),
      "ratio_{0}".format(name): np.sum(np.array(values) > 0.55) / len(values)
  }


def transform_specificity(features):
  return central_tendencies(features["specificities"], "specificity")


def add_scores(scores):
  return {"combined_score": round(sum(scores), 5)}


def transform_combined_score(features):
  return add_scores(features["combination_score"])


TRANSFORM_MAP = {
    pipeline_lib.FeatureType.ARGUMENT: transform_argument,
    pipeline_lib.FeatureType.ASPECT: transform_aspect,
    pipeline_lib.FeatureType.POLITENESS: lambda x: x,
    pipeline_lib.FeatureType.SPECIFICITY: transform_specificity,
    pipeline_lib.FeatureType.LENGTH: lambda x: x,
    pipeline_lib.FeatureType.COMBINED: transform_combined_score
}


def get_feature_obj(dir_name, feature_type):
  with open(dir_name + "/" + feature_type + "_features.json", 'r') as f:
    return json.load(f)


def main():

  args = parser.parse_args()

  overall_features = collections.defaultdict(dict)

  for feature_name in pipeline_lib.FeatureType.ALL:
    for review_id, features in get_feature_obj(args.run_directory,
                                               feature_name).items():
      overall_features[review_id].update(TRANSFORM_MAP[feature_name](features))

  print(args.run_directory + "/final_features.json")

  with open(args.run_directory + "/final_features.json", 'w') as f:
    json.dump(overall_features, f)


if __name__ == "__main__":
  main()
