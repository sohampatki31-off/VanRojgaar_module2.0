import '../models/ask.dart';
import 'livelihood_api.dart';

/// The one door the Ask screen uses. Every question is answered on the server (the safety check,
/// the report-only answer and the number check all live there), so there is nothing to answer
/// offline: a [NetworkException] is shown as "No internet right now".
abstract class AskRepository {
  /// Ask a typed [question] or tap a suggestion ([chip]); exactly one of them.
  Future<AskReply> ask({String? question, String? chip, required String lang});

  /// His earlier questions and answers, and the suggestions for his report.
  Future<AskHistory> history();

  /// Delete everything he asked (rule L8).
  Future<void> clear();
}

class RemoteAskRepository implements AskRepository {
  RemoteAskRepository(this._api);

  final LivelihoodApi _api;

  @override
  Future<AskReply> ask({
    String? question,
    String? chip,
    required String lang,
  }) async {
    final raw = await _api.post('/livelihood/ask', body: {
      if (question != null) 'question': question,
      if (chip != null) 'chip': chip,
      'lang': lang,
    }) as Map<String, dynamic>;
    return AskReply.fromJson(raw);
  }

  @override
  Future<AskHistory> history() async {
    final raw =
        await _api.get('/livelihood/ask/history') as Map<String, dynamic>;
    return AskHistory.fromJson(raw);
  }

  @override
  Future<void> clear() async {
    await _api.delete('/livelihood/ask/history');
  }
}

/// For the standalone demo with no server: asking needs the server, so say so plainly.
class OfflineAskRepository implements AskRepository {
  const OfflineAskRepository();

  @override
  Future<AskReply> ask(
          {String? question, String? chip, required String lang}) =>
      Future.error(const NetworkException());

  @override
  Future<AskHistory> history() => Future.value(const AskHistory());

  @override
  Future<void> clear() => Future.value();
}
