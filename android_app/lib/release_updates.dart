import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

/// APK update checks are based on public GitHub Releases.
/// Publish a release with an APK asset for this checker to notify users.
class ReleaseUpdateService {
  static const String currentVersion = '1.0.2';
  static const String releasesApi =
      'https://api.github.com/repos/bhushanscience/bhushan-science-bot/releases/latest';
  static bool _dialogVisible = false;
  static Timer? _periodicTimer;

  static Future<void> start() async {
    await Future<void>.delayed(const Duration(seconds: 2));
    await checkAndPrompt();
    _periodicTimer ??= Timer.periodic(
      const Duration(hours: 6),
      (_) => unawaited(checkAndPrompt()),
    );
  }

  static List<int> _versionParts(String value) {
    final cleaned = value.trim().replaceFirst(RegExp(r'^[vV]'), '');
    final match = RegExp(r'^(\d+(?:\.\d+)*)').firstMatch(cleaned);
    if (match == null) return const [0];
    return match.group(1)!.split('.').map((part) => int.tryParse(part) ?? 0).toList();
  }

  static bool _isNewer(String candidate, String current) {
    final a = _versionParts(candidate);
    final b = _versionParts(current);
    final length = a.length > b.length ? a.length : b.length;
    for (var i = 0; i < length; i++) {
      final left = i < a.length ? a[i] : 0;
      final right = i < b.length ? b[i] : 0;
      if (left != right) return left > right;
    }
    return false;
  }

  static Future<void> checkAndPrompt({bool forceCheck = false}) async {
    if (_dialogVisible) return;
    try {
      final response = await http.get(
        Uri.parse(releasesApi),
        headers: const {
          'Accept': 'application/vnd.github+json',
          'Cache-Control': 'no-cache',
        },
      ).timeout(const Duration(seconds: 12));
      if (response.statusCode != 200) {
        if (forceCheck) _showStatus('Update check failed (HTTP ${response.statusCode}).');
        return;
      }
      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        if (forceCheck) _showStatus('GitHub release response was invalid.');
        return;
      }
      final tag = (decoded['tag_name'] ?? '').toString();
      final releaseUrl = (decoded['html_url'] ?? '').toString();
      final assets = decoded['assets'];
      final hasApk = assets is List && assets.any((asset) =>
          asset is Map && (asset['name']?.toString().toLowerCase().endsWith('.apk') ?? false));
      if (tag.isEmpty || releaseUrl.isEmpty || !hasApk) {
        if (forceCheck) _showStatus('No published APK release was found yet.');
        return;
      }
      if (!_isNewer(tag, currentVersion)) {
        if (forceCheck) _showStatus('You are using the latest app version ($currentVersion).');
        return;
      }
      final context = appNavigatorKey.currentState?.overlay?.context;
      if (context == null || !context.mounted) return;
      _dialogVisible = true;
      final notes = (decoded['body'] ?? '').toString().trim();
      await showDialog<void>(
        context: context,
        barrierDismissible: true,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Bhushan Science update available'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Version $tag is available. Your version: $currentVersion.'),
                if (notes.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  const Text('Release notes', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(notes.length > 1200 ? notes.substring(0, 1200) : notes),
                ],
                const SizedBox(height: 12),
                const Text('The release page opens so you can download and install the APK. Android may ask you to allow installs from your browser.'),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Later'),
            ),
            FilledButton(
              onPressed: () async {
                final uri = Uri.tryParse(releaseUrl);
                if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              },
              child: const Text('Open update'),
            ),
          ],
        ),
      );
      _dialogVisible = false;
    } catch (_) {
      if (forceCheck) _showStatus('Could not check updates. Check your internet connection.');
      _dialogVisible = false;
    }
  }

  static void _showStatus(String message) {
    final context = appNavigatorKey.currentState?.overlay?.context;
    if (context == null || !context.mounted) return;
    ScaffoldMessenger.maybeOf(context)?.showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}
