var hooks = require('hooks'),
    assert = require('chai').assert;

var params = {version: 'v1', region: 'foo_region', period: 'day'};
var paramsBadVersion = {version: 'VI', region: 'foo_region', period: 'day'};
var paramsBadRegion = {version: 'v1', region: 'strange-region', period: 'day'};
var paramsBadPeriod = {version: 'v1', region: 'foo_region', period: 'otherday'};

hooks.before('GET /api/{version}/regions -> 200', function (test, done) {
  test.request.params = params;
  done();
});

hooks.before('GET /api/{version}/region/{region}/availability/{period} -> 200', function (test, done) {
  test.request.params = params;
  done();
});

hooks.before('GET /api/{version}/region/{region}/availability/{period} -> 404', function (test, done) {
  test.request.params = paramsBadPeriod;
  done();
});

hooks.before('GET /api/{version}/availability/{period} -> 200', function (test, done) {
  test.request.params = params;
  done();
});
