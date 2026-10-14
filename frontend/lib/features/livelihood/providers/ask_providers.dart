import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ask_repository.dart';
import '../data/error_mapping.dart';
import '../models/ask.dart';
import 'livelihood_providers.dart';

final askRepositoryProvider = Provider<AskRepository>(
  (ref) => RemoteAskRepository(ref.watch(livelihoodApiProvider)),
);

class AskState {
  const AskState({
    this.turns = const [],
    this.chips = const [],
    this.hasReport = false,
    this.loading = false,
    this.busy = false,
    this.errorKey,
  });

  final List<ChatTurn> turns;
  final List<SuggestedQuestion> chips;
  final bool hasReport;

  /// Loading the history when the screen opens.
  final bool loading;

  /// A question is on its way.
  final bool busy;

  /// The string key of a plain-language problem ("No internet right now"), or null.
  final String? errorKey;

  AskState copyWith({
    List<ChatTurn>? turns,
    List<SuggestedQuestion>? chips,
    bool? hasReport,
    bool? loading,
    bool? busy,
    String? errorKey,
    bool clearError = false,
  }) =>
      AskState(
        turns: turns ?? this.turns,
        chips: chips ?? this.chips,
        hasReport: hasReport ?? this.hasReport,
        loading: loading ?? this.loading,
        busy: busy ?? this.busy,
        errorKey: clearError ? null : (errorKey ?? this.errorKey),
      );
}

class AskController extends StateNotifier<AskState> {
  AskController(this._repo) : super(const AskState());

  final AskRepository _repo;

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final h = await _repo.history();
      state = state.copyWith(
        turns: h.turns,
        chips: h.chips,
        hasReport: h.hasReport,
        loading: false,
      );
    } catch (e) {
      state = state.copyWith(loading: false, errorKey: errorMessageKey(e));
    }
  }

  /// Send a typed question or tap a suggestion. Nothing is added to the conversation unless the
  /// server answered: a failure shows its message and keeps what he had.
  Future<bool> send(
      {String? question, String? chip, required String lang}) async {
    if (state.busy) return false;
    state = state.copyWith(busy: true, clearError: true);
    try {
      final reply = await _repo.ask(question: question, chip: chip, lang: lang);
      state = state.copyWith(
        turns: [...state.turns, reply.turn],
        chips: reply.chips,
        hasReport: true,
        busy: false,
      );
      return true;
    } catch (e) {
      state = state.copyWith(busy: false, errorKey: errorMessageKey(e));
      return false;
    }
  }

  /// Delete his questions (rule L8): on the server first, then on screen.
  Future<void> clear() async {
    try {
      await _repo.clear();
      state = state.copyWith(turns: const [], clearError: true);
    } catch (e) {
      state = state.copyWith(errorKey: errorMessageKey(e));
    }
  }
}

final askProvider = StateNotifierProvider.autoDispose<AskController, AskState>(
  (ref) => AskController(ref.watch(askRepositoryProvider)),
);
