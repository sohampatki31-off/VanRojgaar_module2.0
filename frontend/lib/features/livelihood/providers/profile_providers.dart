import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/location_service.dart';
import '../data/profile_repository.dart';
import '../models/profile.dart';

final profileRepositoryProvider = Provider<ProfileRepository>(
  (ref) => MemoryProfileRepository(),
);

final locationServiceProvider = Provider<LocationService>(
  (ref) => const GeolocatorLocationService(),
);

/// His saved details, or null if he has not added any. Synchronous so screens never flicker;
/// the repository does the saving behind it.
class ProfileController extends StateNotifier<LivelihoodProfile?> {
  ProfileController(this._repo) : super(null);

  final ProfileRepository _repo;

  Future<void> load() async => state = await _repo.load();

  Future<void> save(LivelihoodProfile profile) async {
    await _repo.save(profile);
    state = profile;
  }

  /// Delete his answers (rule L8).
  Future<void> delete() async {
    await _repo.delete();
    state = null;
  }
}

final profileProvider =
    StateNotifierProvider<ProfileController, LivelihoodProfile?>(
      (ref) => ProfileController(ref.watch(profileRepositoryProvider)),
    );
