from flask import Flask
from flask import render_template, request, jsonify
from sumologic import SumoLogic
import bleach
from collections import defaultdict
from copy import deepcopy
from time import sleep

app = Flask(__name__)
app.debug = True

uneditableSourceFields = ['alive', 'id', 'selected', 'sourceType']

def fixBooleans(payload):
    # Even more Grrrrr: FIX
    # Boolean values come through as strings.  Does this get any more painful?
    for grrr in ['automaticDateParsing', 'forceTimeZone', 'multilineProcessingEnabled', 'useAutolineMatching']:
        if grrr in payload and not isinstance(payload[grrr], bool):
            if payload[grrr].lower() == 'false':
                payload[grrr] = False
            else:
                payload[grrr] = True

    return payload

@app.route("/")
def hello():
    return render_template('index.html')


@app.route("/getCollectors", methods=['POST'])
def getCollectors():
    error = None

    try:
        apiid = bleach.clean(request.json['apiid'])
        apikey = bleach.clean(request.json['apikey'])
    except Exception as error:
        return render_template('index.html', error="Problem with your API keys")

    sumo = SumoLogic(apiid, apikey)
    data = sumo.collectors()

    return jsonify(results = data)


@app.route("/getSources", methods=['POST'])
def getSources():

    """
    We're going to build a big ol' data structure that, in the end,
    should look something like this:

    sourceinfo = {
        'all_sources': {
            8583428: [{COMPLETE SOURCE OBJECT}],
            8583111: [{COMPLETE SOURCE OBJECT}],
            8583846: [{COMPLETE SOURCE OBJECT}],
            8583298: [{COMPLETE SOURCE OBJECT}]
        },
        'source_names': {
            'Friendly Source Name #1': {
                'memberids': [8583428, 8583111],
                'flattened' : {FLATTENED OBJECT VALUES},
                'ignore': {},
                'collectors': ['prodweb01', 'stagedb02']
            },
            'Friendly Source Name #2': {
                'memberids': [8583846, 8583298],
                'flattened': {
                    'something like this': "",
                    'category': ['System', 'System2'],
                    'encoding': ['UTF-8', 'ISO-8859-1']
                },
            }
        },
        'collector_map': {
            8583422: [8583428, 8583111],
            8583401: [8583846, 8583298],
        }
    }
    """

    sourceinfo = {
        'all_sources': {},
        'source_names': {},
        'collector_map': {}
    }

    data = request.json
    sumo = SumoLogic(data['apiid'], data['apikey'])

    for collector in data['collectors']:
        # Get each collector's source from Sumo & store locally:

        sources = sumo.sources(collector['id'])
        sleep(0.15)

        # Add a key of the collector's id to the map. This map maps
        # sources to collectors so we don't have to keep asking Sumo.
        if collector['id'] not in sourceinfo['collector_map']:
            sourceinfo['collector_map'][collector['id']] = []

        for source in sources:

            # Add to the main sourceinfo list of all sources
            if source['id'] not in sourceinfo['all_sources']:
                sourceinfo['all_sources'][source['id']] = source

            # We need to group the sources by their name, but keep their
            # data in the original format, so we'll make a dictionary of
            # names and a list of source ids that have them:
            if source['name'] not in sourceinfo['source_names']:
                sourceinfo['source_names'][source['name']] = {'memberids': [],
                                                              'flattened': {},
                                                              'ignore': {},
                                                              'collectors': []}

            sourceinfo['source_names'][source['name']]['memberids'].append(source['id'])
            sourceinfo['source_names'][source['name']]['collectors'].append(collector['name'])

            # Update the collector_map with this source's key
            sourceinfo['collector_map'][collector['id']].append(source['id'])

    # Finally, we're grouping the sources together by name for bulk editing
    # so we'll check to see if there are any sources that differ from
    # each other using sets.  The best way to do this is to go through the
    # sources that are listed with the same source_names:

    for sourcename in sourceinfo['source_names']:

        # Each unique source name has members. Those member's
        # values will be flattened into the flattener!
        flattener = defaultdict(set)
        for memberid in sourceinfo['source_names'][sourcename]['memberids']:
            for srckey,srcval in sourceinfo['all_sources'][memberid].iteritems():
                # Sets don't like lists. Unpacking accomplishes almost the same goal
                if isinstance(srcval, list):
                    for item in srcval:
                        flattener[srckey].add(item)
                else:
                    flattener[srckey].add(srcval)

        # What got flattened?
        # Since we have to tie the Angular data model to a flattened version (sigh)
        # we build this flattened dict instead of using the original sources. It
        # makes things hard in the long run, but it kinda has to be that way:
        for k,v in flattener.iteritems():
            if k not in uneditableSourceFields:
                if len(v) == 1:
                    sourceinfo['source_names'][sourcename]['flattened'][k] = list(v)[0]
                elif len(v) > 1:
                    sourceinfo['source_names'][sourcename]['flattened'][k] = list(v)
                elif len(v) == 0:
                    sourceinfo['source_names'][sourcename]['flattened'][k] = []

        # Not all values are returned with every API call.
        # Blacklist is one of them, but it needs to be here
        # in order to be rendered in the template.  This
        # should be handled better eventually. TODO
        if 'blacklist' not in flattener:
            sourceinfo['source_names'][sourcename]['flattened']['blacklist'] = []

    # That's it.  Just return that to Angular
    return jsonify(results = sourceinfo)


@app.route("/putCollectors", methods=['POST'])
def putCollectors():

    data = request.json
    sumo = SumoLogic(data['apiid'], data['apikey'])
    response = { 'errors' : [],
                 'success': []}

    # Go through each collector in the collector_map:
    for collectorid in data['collector_map'].keys():

        # Go through each source for a collector listed in the collector map
        for sourceid in data['collector_map'][collectorid]:

            # Find the souce that matches the name (they're by name, for UI)
            for sourcename in data['source_names'].keys():

                # Do we skip this source altogether? (Over)Complicated by transient nature of 'selected'
                if not 'selected' in data['source_names'][sourcename] or ('selected' in data['source_names'][sourcename] and not data['source_names'][sourcename]['selected']):

                    # If there's a match, send the source to Sumo for update
                    if sourceid in data['source_names'][sourcename]['memberids']:

                        # Are we just here to delete?
                        if 'delete' in data['source_names'][sourcename] and data['source_names'][sourcename]['delete'] == True:
                            print "- Deleting collector %s's source %s named %s." % (collectorid, str(sourceid), sourcename)
                            result = sumo.delete_source(collectorid, {'source': {'id': sourceid }})
                            print "- Delete Source: %s" % result.status_code
                        else:
                            # We'll be mutating this, so keep the original re-usable
                            sourcepayload = deepcopy(data['source_names'][sourcename]['flattened'])

                            # Blacklists must be a list of path expressions, or missing:
                            if 'blacklist' in sourcepayload and not isinstance(sourcepayload['blacklist'], list):
                                blklst = []
                                [blklst.append(blacklist.strip()) for blacklist in sourcepayload['blacklist'].split(",")]
                                sourcepayload['blacklist'] = blklst

                            # Remove keys marked to be ignored
                            for ignorekey in data['source_names'][sourcename]['ignore']:
                                if ignorekey in sourcepayload:
                                    del sourcepayload[ignorekey]

                            # The ID is deliberately absent from the flattened data, add
                            sourcepayload['id'] = sourceid

                            # Grrrrr:
                            # "All modifiable fields must be provided, and all immutable
                            # fields must match those existing in the system." --Sumo
                            sourcepayload['sourceType'] = data['all_sources'][str(sourceid)]['sourceType']

                            # Convert boolean string to booleans
                            sourcepayload = fixBooleans(sourcepayload)

                            print "+ Updating Collector %s's source %s named %s" % (collectorid, sourceid, sourcename)

                            # You have to get the etag from a collector call
                            # TODO: refactor the initial fetch to include this somehow.
                            throwaway, etag = sumo.source(collectorid, sourceid)
                            result = sumo.update_source(collectorid, {'source': sourcepayload}, etag)
                            sleep(0.15)

                            print "+ Source Update: %s" % result.status_code #, result.text)

                            # if str(result.status_code).startswith("2"):
                            #     response['success'].append(result)
                            # else:
                            #     response['errors'].append(result)

                        break
                else:
                    print ". Skipping source %s" % sourcename

    # TODO: actually return useful information
    return jsonify(results = response)


@app.route("/addCollector", methods=['POST'])
def addCollector():

    data = request.json
    sumo = SumoLogic(data['apiid'], data['apikey'])
    response = { 'errors' : [],
                 'success': []}

    params = {}
    remove = ('apiid', 'apikey', 'collectors', 'selected')
    for key in data.keys():
        if key not in remove:
            params[key] = data[key]

    # Convert boolean string to booleans
    payload = {'source': fixBooleans(params)}

    for collector in data['collectors']:
        endpoint = '/collectors/%s/sources' % collector['id']
        response = sumo.post(endpoint, payload)
        sleep(0.15)

    # TODO: actually return useful information
    return jsonify(results = response)


if __name__ == "__main__":
    app.run()
