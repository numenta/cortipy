# cortipy [![Build Status](https://travis-ci.org/numenta/cortipy.svg?branch=master)](https://travis-ci.org/numenta/cortipy) [![Coverage Status](https://coveralls.io/repos/numenta/cortipy/badge.svg?branch=master)](https://coveralls.io/r/numenta/cortipy?branch=master)

Numenta's Cortical.io REST API client in Python.

This is not the official Cortical.io Python REST client for their API. You can find the official client at https://github.com/cortical-io/python-client-sdk.


## Installation
You must have a valid REST API key from [Cortical.io](http://www.cortical.io/developers.html).

To install, run:

    python setup.py install

Then, set up the following environment variables with your REST API credentials:

    export CORTICAL_API_KEY=api_key

## Usage

### Classification Example
	import cortipy
	import os
	
	# Init API client
	apiKey = os.environ.get('CORTICAL_API_KEY')
	client = cortipy.CorticalClient(apiKey)

	# Create the category with some positive (and negative) examples, and a name.
	pos = [
		"Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live.",
      	"To iterate is human, to recurse divine.",
	    "First learn computer science and all the theory. Next develop a programming style. Then forget all that and just hack.",
	    "Beautiful is better than ugly."
	    ]
	neg = [
		"To err is human, to forgive divine."
		]
	categoryName = "programming quotes"
	programmingCategory = client.createClassification(categoryName, pos, neg)
	
	# Evaluate how close a new term is to the category.
	termBitmap = client.getBitmap("Python")['fingerprint']['positions']
	distances = client.compare(termBitmap, programmingCategory['positions'])
	print distances['euclideanDistance']
	
	# Try a block of text.
	textBitmap = client.getTextBitmap("The Zen of Python >>>import this")['fingerprint']['positions']
	distances = client.compare(textBitmap, programmingCategory['positions'])
	print distances['euclideanDistance']
