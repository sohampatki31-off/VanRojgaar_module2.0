import '../models/profile.dart';

/// Where his saved details live. Module 2 keeps them in memory; module 3 adds the phone's
/// encrypted storage and the server behind this same interface, so no screen changes.
abstract class ProfileRepository {
  Future<LivelihoodProfile?> load();
  Future<void> save(LivelihoodProfile profile);

  /// Delete his answers (rule L8). Deleting nothing is not an error.
  Future<void> delete();
}

class MemoryProfileRepository implements ProfileRepository {
  LivelihoodProfile? _profile;

  @override
  Future<LivelihoodProfile?> load() async => _profile;

  @override
  Future<void> save(LivelihoodProfile profile) async => _profile = profile;

  @override
  Future<void> delete() async => _profile = null;
}
