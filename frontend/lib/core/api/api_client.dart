import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

// A small copy of the host's ApiClient (vanmitra_tem/lib/core/api/api_client.dart), with the
// same ApiException fields and the same error body {error, message_key, rule?, details}, so the
// host's own client can replace this file at merge without touching the feature.

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

/// There was no usable answer at all: no network, a timeout, or a reply that was not JSON.
/// The app treats this as "offline" and keeps working from what is on the phone.
class NetworkException implements Exception {
  const NetworkException([this.cause]);
  final Object? cause;

  @override
  String toString() => 'NetworkException($cause)';
}

typedef TokenProvider = Future<String?> Function();

class ApiClient {
  ApiClient({
    required this.baseUrl,
    this.tokenProvider,
    http.Client? client,
    this.timeout = const Duration(seconds: 20),
  }) : _client = client ?? http.Client();

  /// With or without a trailing slash, and with or without `/api/v1` (same as the host).
  final String baseUrl;
  final Duration timeout;
  final TokenProvider? tokenProvider;
  final http.Client _client;

  String get _root {
    final trimmed = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    return trimmed.endsWith('/api/v1') ? trimmed : '$trimmed/api/v1';
  }

  Future<Map<String, String>> _headers() async {
    final token = await tokenProvider?.call();
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> _send(
    Future<http.Response> Function(Uri uri, Map<String, String> headers) call,
    String path,
  ) async {
    final uri = Uri.parse('$_root$path');
    final http.Response response;
    try {
      response = await call(uri, await _headers()).timeout(timeout);
    } on TimeoutException catch (e) {
      throw NetworkException(e);
    } on SocketException catch (e) {
      throw NetworkException(e);
    } on http.ClientException catch (e) {
      throw NetworkException(e);
    }
    return _handle(response);
  }

  dynamic _handle(http.Response response) {
    // Always UTF-8: the server sends Marathi text, and without a charset the http package
    // would read it as Latin-1 (the same care the host takes).
    final text = utf8.decode(response.bodyBytes);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (text.isEmpty) return null;
      try {
        return jsonDecode(text);
      } on FormatException catch (e) {
        throw NetworkException(
          e,
        ); // a captive portal or proxy page, not our server
      }
    }
    try {
      final body = jsonDecode(text);
      if (body is Map<String, dynamic> && body.containsKey('message_key')) {
        throw ApiException.fromJson(response.statusCode, body);
      }
    } on FormatException {
      // fall through: not our error body
    }
    throw ApiException(
      statusCode: response.statusCode,
      error: 'SERVER_ERROR',
      messageKey: response.statusCode >= 500 ? 'error.server' : 'error.unknown',
    );
  }

  Future<dynamic> get(String path) =>
      _send((u, h) => _client.get(u, headers: h), path);

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) => _send(
    (u, h) => _client.post(
      u,
      headers: h,
      body: body == null ? null : jsonEncode(body),
    ),
    path,
  );

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) => _send(
    (u, h) => _client.put(
      u,
      headers: h,
      body: body == null ? null : jsonEncode(body),
    ),
    path,
  );

  Future<dynamic> delete(String path) =>
      _send((u, h) => _client.delete(u, headers: h), path);
}
