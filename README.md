# argcheck for python programs

This is a minimum version for checking the input argument dict. 
It would examine argument's type,  as well as keys and types of its sub-arguments. 

A special case called *variant* is also handled, 
where you can determine the items of a dict based the value of on one of its "flag" key. 

## TODO

- [ ] recursive generation of docs
- [ ] interface for adding sub arguments and variants (maybe follow `argparse`)
- [ ] possibly support of indexing by keys
- [ ] possibly support of generate default dicts (may not be a good idea)