# Argument checking for python programs

This is a minimum version for checking the input argument dict. 
It would examine argument's type,  as well as keys and types of its sub-arguments. 

A special case called *variant* is also handled, 
where you can determine the items of a dict based the value of on one of its `flag_name` key. 

There are three main methods of `Argument` class:

- `check` method that takes a dict and see if its type follows the definition in the class
- `normalize` method that takes a dict and convert alias and add default value into it
- `gendoc` method that outputs the defined argument structure and corresponding docs

There are also `check_value` and `normalize_value` that 
ignore the leading key comparing to the base version.

When targeting to html rendering, additional anchor can be made for cross reference. 
Set `make_anchor=True` when calling `gendoc` function and use standard ref syntax in rst.
The id is the same as the argument path. Variant types would be in square brackets.

Please refer to test files for detailed usage.


## TODO

- [ ] possibly support of indexing by keys
