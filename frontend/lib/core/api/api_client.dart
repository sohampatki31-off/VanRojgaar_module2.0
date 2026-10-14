import 'dart:convert';

import 'package:http/http.dart' as http;

// STANDALONE STAND-IN for the host's ApiClient (vanmitra_tem/lib/core/api/api_client.dart). It has
// the same public surface the feature uses (get/post/put/delete returning decoded JSON, and
// ApiException with the same fields), and, like the host's, it throws raw socket errors and has no
// timeout: the feature's HostApiAdapter adds both. At merge this file is NOT copied: the host's
// own client is used.

/// The server answered with an error. `messageKey` is what the app turns into plain words.
class ApiException implements Exception {
  ApiException({
    required this.statusCode,
    required this.error,
    required this.messageKey,
    this.rule,
    this.details,
  });

  final int statusCode;
  final String error;
  final String messageKey;
  final String? rule;
  final Map<String, dynamic>? details;

  factory ApiException.fromJson(int statusCode, Map<String, dynamic> json) =>
      ApiException(
        statusCode: statusCode,
        error: (json['error'] as String?) ?? 'UNKNOWN_ERROR',
        messageKey: (json['message_key'] as String?) ?? 'error.unknown',
        rule: json['rule'] as String?,
        details: json['details'] as Map<String, dynamic>?,
      );

  @override
  String toString() => 'ApiException($statusCode $error $messageKey)';
}

typedef TokenProvider = Future<String?> Function();

class ApiClient {
  /// With no arguments it reads the address and a development token from `--dart-define`
  /// (VANMITRA_API_BASE_URL, VANMITRA_DEV_TOKEN), so `ApiClient()` works here and in the host.
  ApiClient({String? baseUrl, this.tokenProvider, http.Client? client})
      : baseUrl =
            baseUrl ?? const String.fromEnvironment('VANMITRA_API_BASE_URL'),
        _client = client ?? http.Client();

  final String baseUrl;
  final TokenProvider? tokenProvider;
  final http.Client _client;

  String get _root {
    final trimmed = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return trimmed.endsWith('/api/v1') ? trimmed : '$trimmed/api/v1';
  }

  Future<Map<String, String>> _headers() async {
    final token = tokenProvider != null
        ? await tokenProvider!()
        : const String.fromEnvironment('VANMITRA_DEV_TOKEN');
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  dynamic _handle(http.Response response) {
    // Always UTF-8: the server sends Marathi text, and without a charset the http package would
    // read it as Latin-1 (the same care the host takes).
    final text = utf8.decode(response.bodyBytes);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.bodyBytes.isEmpty) return null;
      return jsonDecode(
          text); // a FormatException here is mapped by the adapter
    }
    try {
      final body = jsonDecode(text);
      if (body is Map<String, dynamic>) {
        throw ApiException.fromJson(response.statusCode, body);
      }
    } on FormatException {
      // not our error body
    }
    throw ApiException(
      statusCode: response.statusCode,
      error: 'NETWORK_OR_SERVER_ERROR',
      messageKey: 'error.network_or_server',
    );
  }

  Future<dynamic> get(String path) async => _handle(
      await _client.get(Uri.parse('$_root$path'), headers: await _headers()));

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async =>
      _handle(
        await _client.post(
          Uri.parse('$_root$path'),
          headers: await _headers(),
          body: body != null ? jsonEncode(body) : null,
        ),
      );

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async =>
      _handle(
        await _client.put(
          Uri.parse('$_root$path'),
          headers: await _headers(),
          body: body != null ? jsonEncode(body) : null,
        ),
      );

  Future<dynamic> delete(String path) async => _handle(await _client
      .delete(Uri.parse('$_root$path'), headers: await _headers()));
}
