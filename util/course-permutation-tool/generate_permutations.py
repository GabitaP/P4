#!/usr/bin/env python
#
# Create a file of course permutations based on permutations.json file configuration. A max
# of 3 fields can be chosen to build permutations on, and only the fields under
# "permutation_data" are eligible. No field input pulls from "default_data"
#
# ./generate_permutations.py --seed_data_file permutations.json --fields field1 field2 field3

import argparse
import json
import datetime
import pytz
import sys

# course defaults
COURSE_NUMBER = None
COURSE_ORGANIZATION = "RITX"
COURSE_RUN = "3T2017"
COURSE_USER = "edx@example.com"
COURSE_PARTNER = "edx"

# date configurations
FUTURE_DATE = "future"
PAST_DATE = "past"

TEST_COURSES_FILE = "test_courses.json"


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed_data_file', help="Input a permutation configuration file")
    parser.add_argument('--fields', nargs="*", action="append", default=None,
                        help="Specify which fields to generate permutations on")

    return parser.parse_args()


def process_field_arguments(parser_args):
    try:
        file = open(parser_args.seed_data_file)
        file_data = json.load(file)
        default_data = file_data["default_data"]
        permutation_data = file_data["permutation_data"]
        default_data_keys = permutation_data.keys()
    except IOError:
        print("Please fix your input file - {}".format(sys.exc_value))
        sys.exit()
    except KeyError:
        print("Could not find key {}".format(sys.exc_value))
        sys.exit()

    field_args = {}
    parsed_field_args = parser_args.fields

    # if no field arguments are given, just return default data
    if not parsed_field_args:
        field_args = file_data["default_data"]
    else:
        num_field_args = len(parsed_field_args[0])
        if (num_field_args > 3):
            raise argparse.ArgumentTypeError("Only a max of 3 fields allowed")
        # add each command line field to fields dict
        for field in parsed_field_args[0]:
            try:
                field_args[field] = permutation_data[field]
            except KeyError:
                print "{} is not a field option".format(sys.exc_value)
                sys.exit()

        # calculate the difference between all possible fields and the chosen permutation ones
        default_fields = list(set(default_data_keys) - set(parsed_field_args[0]))

        # add non permutation fields to dict
        for field in default_fields:
            field_args[field] = default_data[field]

    return field_args


def generate_permutations(field_args, index, results, courses_dict, field_values_dict):
    all_permutations_keys = field_args.keys()
    permutation_option = all_permutations_keys[index]
    permutations_values = field_args[permutation_option]

    for permutation_value in permutations_values:
        # add other required course and enrollment default fields to dict
        # will be generated automatically by course creation script
        courses_dict["number"] = COURSE_NUMBER
        courses_dict["organization"] = COURSE_ORGANIZATION
        courses_dict["run"] = COURSE_RUN
        courses_dict["user"] = COURSE_USER
        courses_dict["partner"] = COURSE_PARTNER
        # configure enrollment seat settings
        enrollment_dict = {}
        enrollment_dict["credit"] = False
        enrollment_dict["credit_provider"] = "test-credit-provider"

        # add permutation fields to dict
        field_values_dict[permutation_option] = permutation_value

        # generate start and end dates
        if permutation_option in ["start", "end"]:
            permutation_value = calculate_date_value(permutation_value)
        field_values_dict[permutation_option] = permutation_value

        for permutation_key in all_permutations_keys:
            # add audit and verify fields to dict
            if permutation_key == "audit" and permutation_value == True:
                enrollment_dict["audit"] = permutation_value
            if permutation_key == "verify" and permutation_value == True:
                enrollment_dict["verify"] = True

        if index + 1 < len(all_permutations_keys):
            generate_permutations(field_args, index + 1, results, courses_dict, field_values_dict)

        courses_dict["enrollment"] = enrollment_dict
        courses_dict["fields"] = field_values_dict.copy()
        results.append(courses_dict.copy())

    # needed to match course input file creation
    wrapper_courses_dict = {}
    wrapper_courses_dict["courses"] = results

    create_courses_json_file(wrapper_courses_dict)


def create_courses_json_file(wrapper_courses_dict):
    with open(TEST_COURSES_FILE, "w") as outfile:
        json.dump(wrapper_courses_dict, outfile)


def calculate_date_value(date_const):
    now = datetime.datetime.now(pytz.UTC)
    try:
        if date_const == FUTURE_DATE:
            future = str(now + datetime.timedelta(days=365))
            return future
        if date_const == PAST_DATE:
            past = str(now - datetime.timedelta(days=60))
            return past
        if date_const == None:
            return None
    except ValueError:
        print "Dates can only be future or past"


def start_field_recursion(process_field_args):
    generate_permutations(process_field_args, 0, [], {}, {})


if __name__ == "__main__":
    args = arg_parse()
    process_field_args = process_field_arguments(args)
    start_field_recursion(process_field_args)