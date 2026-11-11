import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const String defaultUpdateServer = 'https://bhushan-science-bot.onrender.com';

class RemoteUpdateService {
  static final ValueNotifier<Map<String, dynamic>?> manifest = ValueNotifier(null);
  static const String _cacheKey = 'bhushan.remote_update_manifest.v1';

  static String _base(String value) =>
      value.trim().replaceFirst(RegExp(r'/+$'), '');

  static Future<Map<String, dynamic>> fetchManifest(String baseUrl) async {
    final response = await http
        .get(
          Uri.parse('${_base(baseUrl)}/api/v1/updates/manifest'),
          headers: const {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
          },
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw Exception('Update server returned HTTP ${response.statusCode}.');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! Map ||
        decoded['version'] is! int ||
        decoded['payload'] is! Map) {
      throw const FormatException('Update manifest format is invalid.');
    }
    final result = Map<String, dynamic>.from(decoded);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cacheKey, jsonEncode(result));
    manifest.value = result;
    return result;
  }

  static Future<Map<String, dynamic>?> readCachedManifest() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_cacheKey);
    if (raw == null) return null;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map) {
        final result = Map<String, dynamic>.from(decoded);
        manifest.value = result;
        return result;
      }
    } catch (_) {
      // Ignore invalid local cache.
    }
    return null;
  }

  static Future<void> syncOnStartup() async {
    await readCachedManifest();
    try {
      await fetchManifest(defaultUpdateServer);
    } catch (_) {
      // Retain the cached manifest when offline or server is unavailable.
    }
  }

  static Future<bool> verifyAdminKey({
    required String baseUrl,
    required String adminKey,
  }) async {
    final response = await http
        .post(
          Uri.parse('${_base(baseUrl)}/api/v1/admin/auth/check'),
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey,
          },
          body: '{}',
        )
        .timeout(const Duration(seconds: 15));
    return response.statusCode == 200;
  }

  static Future<Map<String, dynamic>> publish({
    required String baseUrl,
    required String adminKey,
    required String releaseNotes,
    required Map<String, dynamic> payload,
  }) async {
    final response = await http
        .post(
          Uri.parse('${_base(baseUrl)}/api/v1/admin/updates'),
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Admin-Key': adminKey,
          },
          body: jsonEncode({
            'release_notes': releaseNotes,
            'payload': payload,
          }),
        )
        .timeout(const Duration(seconds: 20));
    dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } catch (_) {
      decoded = null;
    }
    if (response.statusCode != 201 || decoded is! Map) {
      final message = decoded is Map ? decoded['error'] : null;
      throw Exception(
        message?.toString() ??
            'Publish failed (HTTP ${response.statusCode}).',
      );
    }
    await fetchManifest(baseUrl);
    return Map<String, dynamic>.from(decoded);
  }
}

class RemoteUpdatePage extends StatefulWidget {
  final String adminKey;
  const RemoteUpdatePage({super.key, required this.adminKey});

  @override
  State<RemoteUpdatePage> createState() => _RemoteUpdatePageState();
}

class _RemoteUpdatePageState extends State<RemoteUpdatePage> {
  final TextEditingController _server =
      TextEditingController(text: defaultUpdateServer);
  final TextEditingController _notes = TextEditingController();
  final TextEditingController _payload = TextEditingController(
    text: '{\n  "announcement": "New study content is available."\n}',
  );
  Map<String, dynamic>? _manifest;
  bool _busy = false;
  String? _status;

  @override
  void initState() {
    super.initState();
    _loadCached();
  }

  Future<void> _loadCached() async {
    final cached = await RemoteUpdateService.readCachedManifest();
    if (mounted && cached != null) setState(() => _manifest = cached);
  }

  Future<void> _check() async {
    setState(() {
      _busy = true;
      _status = null;
    });
    try {
      final value = await RemoteUpdateService.fetchManifest(_server.text);
      if (!mounted) return;
      setState(() {
        _manifest = value;
        _status = 'Connected. Latest content version: ${value['version']}.';
      });
    } catch (error) {
      if (mounted) setState(() => _status = 'Could not sync: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _publish() async {
    setState(() {
      _busy = true;
      _status = null;
    });
    try {
      final decoded = jsonDecode(_payload.text);
      if (decoded is! Map) {
        throw const FormatException('Content must be a JSON object.');
      }
      final result = await RemoteUpdateService.publish(
        baseUrl: _server.text,
        adminKey: widget.adminKey,
        releaseNotes: _notes.text.trim(),
        payload: Map<String, dynamic>.from(decoded),
      );
      if (!mounted) return;
      setState(() {
        _status =
            'Published successfully. Content version ${result['version']} is available.';
      });
      await _check();
    } catch (error) {
      if (mounted) setState(() => _status = 'Publish failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _server.dispose();
    _notes.dispose();
    _payload.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Remote content updates')),
        body: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Text(
              'Publish once, sync to every phone',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              'This updates app content and announcements. It does not install a new APK or change native app code.',
              style: TextStyle(color: Colors.white60),
            ),
            const SizedBox(height: 18),
            TextField(
              controller: _server,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                labelText: 'Update server URL',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _busy ? null : _check,
              icon: const Icon(Icons.sync),
              label: const Text('Check latest update'),
            ),
            if (_manifest != null)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.cloud_done, color: Colors.greenAccent),
                  title: Text('Content version ${_manifest!['version']}'),
                  subtitle: Text(
                    (_manifest!['release_notes'] ?? '').toString().isEmpty
                        ? 'Latest manifest is cached on this phone.'
                        : _manifest!['release_notes'].toString(),
                  ),
                ),
              ),
            const Divider(height: 28),
            const Text(
              'Admin publishing',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notes,
              maxLength: 500,
              decoration: const InputDecoration(
                labelText: 'What changed?',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _payload,
              minLines: 6,
              maxLines: 12,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Content payload (JSON)',
                helperText: 'Example: {"announcement":"New chapter added"}',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _busy ? null : _publish,
              icon: const Icon(Icons.publish),
              label: Text(
                _busy ? 'Please wait…' : 'Publish update to all users',
              ),
            ),
            if (_status != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(
                  _status!,
                  style: const TextStyle(color: Colors.white70),
                ),
              ),
          ],
        ),
      );
}
