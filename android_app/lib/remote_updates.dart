import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const String defaultUpdateServer = 'https://bhushan-science-bot.onrender.com';

class RemoteUpdateService {
  static final ValueNotifier<Map<String, dynamic>?> manifest = ValueNotifier(null);
  static const _cacheKey = 'bhushan.remote_update_manifest.v1';

  static Future<Map<String, dynamic>> fetchManifest(String baseUrl) async {
    final cleanBase = baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final uri = Uri.parse('$cleanBase/api/v1/updates/manifest');
    final response = await http.get(uri, headers: const {
      'Accept': 'application/json',
      'Cache-Control': 'no-cache',
    }).timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw Exception('Update server returned HTTP ${response.statusCode}.');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! Map<String, dynamic> ||
        decoded['version'] is! int ||
        decoded['payload'] is! Map) {
      throw const FormatException('Update manifest format is invalid.');
    }
    final manifest = Map<String, dynamic>.from(decoded);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cacheKey, jsonEncode(manifest));
    RemoteUpdateService.manifest.value = manifest;
    return manifest;
  }

  static Future<Map<String, dynamic>?> readCachedManifest() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_cacheKey);
    if (raw == null) return null;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        manifest.value = decoded;
        return decoded;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  static Future<void> syncOnStartup() async {
    await readCachedManifest();
    try {
      await fetchManifest(defaultUpdateServer);
    } catch (_) {
      // Keep the last verified manifest available for offline use.
    }
  }

  static Future<Map<String, dynamic>> publish({
    required String baseUrl,
    required String adminKey,
    required String releaseNotes,
    required Map<String, dynamic> payload,
  }) async {
    final cleanBase = baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final uri = Uri.parse('$cleanBase/api/v1/admin/updates');
    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Admin-Key': adminKey,
      },
      body: jsonEncode({
        'release_notes': releaseNotes,
        'payload': payload,
      }),
    ).timeout(const Duration(seconds: 20));
    final decoded = jsonDecode(response.body);
    if (response.statusCode != 201 || decoded is! Map<String, dynamic>) {
      final message = decoded is Map ? decoded['error'] : null;
      throw Exception(message?.toString() ?? 'Publish failed (HTTP ${response.statusCode}).');
    }
    await fetchManifest(baseUrl);
    return decoded;
  }
}

class RemoteUpdatePage extends StatefulWidget {
  const RemoteUpdatePage({super.key});

  @override
  State<RemoteUpdatePage> createState() => _RemoteUpdatePageState();
}

class _RemoteUpdatePageState extends State<RemoteUpdatePage> {
  final _server = TextEditingController(text: defaultUpdateServer);
  final _key = TextEditingController();
  final _notes = TextEditingController();
  final _payload = TextEditingController(
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
    setState(() { _busy = true; _status = null; });
    try {
      final manifest = await RemoteUpdateService.fetchManifest(_server.text);
      if (!mounted) return;
      setState(() {
        _manifest = manifest;
        _status = 'Connected. Latest content version: ${manifest['version']}.';
      });
    } catch (error) {
      if (mounted) setState(() => _status = 'Could not sync: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _publish() async {
    if (_key.text.trim().isEmpty) {
      setState(() => _status = 'Enter the admin publishing key configured on the server.');
      return;
    }
    setState(() { _busy = true; _status = null; });
    try {
      final decoded = jsonDecode(_payload.text);
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException('Content must be a JSON object.');
      }
      final result = await RemoteUpdateService.publish(
        baseUrl: _server.text,
        adminKey: _key.text.trim(),
        releaseNotes: _notes.text.trim(),
        payload: decoded,
      );
      if (!mounted) return;
      setState(() => _status = 'Published successfully. Version ${result['version']} is now available to all app installs.');
      _key.clear();
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
    _key.dispose();
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
        const Text('Publish once, sync to every phone', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        const Text('This updates app content and announcements. It does not install a new APK or change native app code.', style: TextStyle(color: Colors.white60)),
        const SizedBox(height: 18),
        TextField(
          controller: _server,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(labelText: 'Update server URL', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: _busy ? null : _check,
          icon: const Icon(Icons.sync),
          label: const Text('Check latest update'),
        ),
        if (_manifest != null) Card(
          child: ListTile(
            leading: const Icon(Icons.cloud_done, color: Colors.greenAccent),
            title: Text('Content version ${_manifest!['version']}'),
            subtitle: Text((_manifest!['release_notes'] ?? '').toString().isEmpty
              ? 'Latest manifest is cached on this phone.'
              : _manifest!['release_notes'].toString()),
          ),
        ),
        const Divider(height: 28),
        const Text('Admin publishing', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextField(
          controller: _key,
          obscureText: true,
          autocorrect: false,
          decoration: const InputDecoration(labelText: 'Admin publishing key', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _notes,
          maxLength: 500,
          decoration: const InputDecoration(labelText: 'What changed?', border: OutlineInputBorder()),
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
          label: Text(_busy ? 'Please wait…' : 'Publish update to all users'),
        ),
        if (_status != null) Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Text(_status!, style: const TextStyle(color: Colors.white70)),
        ),
      ],
    ),
  );
}
