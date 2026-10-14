// STANDALONE ONLY (not copied into the host): tests of the stand-in ApiClient and the adapter's
// error mapping against a mocked HTTP client. In the host the real ApiClient is the host's own.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vanmitra_rozgar/core/api/api_client.dart';
import 'package:vanmitra_rozgar/features/livelihood/data/livelihood_api.dart';

http.Response _json(Object body, [int status = 200]) => http.Response.bytes(
      utf8.encode(jsonEncode(body)),
      status,
      // no charset on purpose: the client must still read Marathi as UTF-8 (the host's care)
      headers: {'content-type': 'application/json'},
    );

http.Response _error(int status, String key, [String error = 'ERR']) =>
    _json({'error': error, 'message_key': key, 'details': {}}, status);

class _Server {
  _Server(this.handler);

  http.Response Function(http.Request) handler;
  final List<http.Request> calls = [];

  LivelihoodApi api({
    String base = 'http://host:8010',
    String? token = 'tok',
    Duration timeout = const Duration(seconds: 5),
  }) =>
      HostApiAdapter(
        ApiClient(
          baseUrl: base,
          tokenProvider: token == null ? null : () async => token,
          client: MockClient((req) async {
            calls.add(req);
            return handler(req);
          }),
        ),
        timeout: timeout,
      );
}

http.Response _offline(http.Request _) =>
    throw const SocketException('no network');

void main() {
  group('ApiClient', () {
    test(
      'builds the URL with or without /api/v1 and a trailing slash',
      () async {
        for (final base in [
          'http://h:8010',
          'http://h:8010/',
          'http://h:8010/api/v1',
          'http://h:8010/api/v1/',
        ]) {
          final s = _Server((_) => _json({'ok': true}));
          await s.api(base: base).get('/livelihood/meta');
          expect(
            s.calls.single.url.toString(),
            'http://h:8010/api/v1/livelihood/meta',
            reason: base,
          );
        }
      },
    );

    test(
        'sends the bearer token and JSON headers, and none when there is no token',
        () async {
      final s = _Server((_) => _json({}));
      await s.api().post('/x', body: {'a': 1});
      expect(s.calls.single.headers['Authorization'], 'Bearer tok');
      expect(
        s.calls.single.headers['Content-Type'],
        contains('application/json'),
      );
      expect(jsonDecode(s.calls.single.body), {'a': 1});

      final anon = _Server((_) => _json({}));
      await anon.api(token: null).get('/x');
      expect(anon.calls.single.headers.containsKey('Authorization'), isFalse);
    });

    test('reads Marathi as UTF-8', () async {
      final s = _Server((_) => _json({'name': 'ओझर'}));
      final body = await s.api().get('/x') as Map<String, dynamic>;
      expect(body['name'], 'ओझर');
    });

    test('an empty 204 answer is null', () async {
      final s = _Server((_) => http.Response('', 204));
      expect(await s.api().delete('/x'), isNull);
    });

    test(
      'a server error body becomes an ApiException with its message key',
      () async {
        final s = _Server(
          (_) => _error(422, 'livelihood.radius_too_large', 'RADIUS_TOO_LARGE'),
        );
        await expectLater(
          s.api().post('/x'),
          throwsA(
            isA<ApiException>()
                .having((e) => e.statusCode, 'status', 422)
                .having(
                  (e) => e.messageKey,
                  'key',
                  'livelihood.radius_too_large',
                )
                .having((e) => e.error, 'error', 'RADIUS_TOO_LARGE'),
          ),
        );
      },
    );

    test('a 500 that is not our JSON is still a clean ApiException', () async {
      final s = _Server((_) => http.Response('<html>Bad gateway</html>', 502));
      await expectLater(
        s.api().get('/x'),
        throwsA(
          isA<ApiException>().having(
            (e) => e.messageKey,
            'key',
            'error.network_or_server',
          ),
        ),
      );
    });

    test(
      'a 200 that is not JSON (a captive portal) counts as offline',
      () async {
        final s = _Server(
          (_) => http.Response('<html>Sign in to Wi-Fi</html>', 200),
        );
        await expectLater(
          s.api().get('/x'),
          throwsA(isA<NetworkException>()),
        );
      },
    );

    test(
      'no network, a timeout and a client error all count as offline',
      () async {
        await expectLater(
          _Server(_offline).api().get('/x'),
          throwsA(isA<NetworkException>()),
        );
        final slow = HostApiAdapter(
          ApiClient(
            baseUrl: 'http://h',
            client: MockClient((_) => Completer<http.Response>().future),
          ),
          timeout: const Duration(milliseconds: 20),
        );
        await expectLater(slow.get('/x'), throwsA(isA<NetworkException>()));
        final broken = HostApiAdapter(
          ApiClient(
            baseUrl: 'http://h',
            client: MockClient(
              (_) async => throw http.ClientException('reset'),
            ),
          ),
        );
        await expectLater(broken.get('/x'), throwsA(isA<NetworkException>()));
      },
    );
  });
}
