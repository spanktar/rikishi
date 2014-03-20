from copy import copy
import json
import requests

class SumoLogic:

	endpoint = 'https://api.sumologic.com/api/v1'
	session = requests.Session()

	def __init__(self, accessId, accessKey):
		self.session.auth = (accessId, accessKey)
		self.session.headers = {'content-type': 'application/json', 'accept': 'application/json'}

	def get(self, method, params=None):
		return self.session.get(self.endpoint + method, params=params)

	def post(self, method, params, headers=None):
		return self.session.post(self.endpoint + method, data=json.dumps(params), headers=headers)

	def put(self, method, params, headers=None):
		return self.session.put(self.endpoint + method, data=json.dumps(params), headers=headers)

	def search(self):
		endpoint = self.endpoint + '/logs/search'

	def search_job(self, query, fromTime, toTime):
		endpoint = self.endpoint + '/search/jobs'
		params = {'query': query, 'from': fromTime, 'to': toTime}
		r = self.post(params)
		if r.status_code == 202:
			return r.headers['Location']
		else:
			raise r.raise_for_status()

	def collectors(self, limit=None, offset=None):
		params = {'limit': limit, 'offset': offset}
		r = self.get('/collectors', params)
		return json.loads(r.text)['collectors']

	def collector(self, collector_id):
		r = self.get('/collectors/' + str(collector_id))
		return json.loads(r.text), r.headers['etag']

	def update_collector(self, collector, etag):
		headers = {'If-Match': etag}
		return self.put('/collectors/' + str(collector['collector']['id']), collector, headers)

	def sources(self, collector_id, limit=None, offset=None):
		params = {'limit': limit, 'offset': offset}
		r = self.get('/collectors/' + str(collector_id) + '/sources', params)
		return json.loads(r.text)['sources']

	def source(self, collector_id, source_id):
		r = self.get('/collectors/' + str(collector_id) + '/sources/' + str(source_id))
		return json.loads(r.text), r.headers['etag']

	def update_source(self, collector_id, source, etag):
		headers = {'If-Match': etag}
		return self.put('/collectors/' + str(collector_id) + '/sources/' + str(source['source']['id']), source, headers)

	def dashboard(self):
		r = self.get('/dashboards', params)

# 1. Create search job
# 2. Poll for completion
# 3. Get results
# 4. Email

'''
def update_collector(collector_etagged_request):
    collector_request = collector_etagged_request.body
    collector_etag = collector_etagged_request.etag

    print "Updating collector: " + collector_request["collector"]["name"]

    http_response = requests.put(endpoint + str(collector_request["collector"]["id"]),
                     auth = auth,
                     data = json.dumps(collector_request),
                     headers = {"Content-Type": "application/json",
                                "If-Match": collector_etag})

    if (http_response.status_code != 200):
        print "Error! Server responded with Status " + str(http_response.status_code)
        print http_response.text

# Main application

prefix = raw_input("Enter prefix of collectors to update:")

listing = list_collectors()

for collector in listing["collectors"]:
   if (collector["name"].startswith(prefix)):
      print "Going to update " + collector["name"]
      update_request = get_collector(collector["id"])
      update_request.body["collector"]["ephemeral"] = True
      update_collector(update_request)
'''
