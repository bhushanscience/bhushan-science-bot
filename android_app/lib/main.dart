import 'dart:async';
import 'package:flutter/material.dart';

void main() => runApp(const BhushanScienceApp());

const _bg = Color(0xFF0B1020);
const _panel = Color(0xFF151D31);
const _accent = Color(0xFF9EA4FF);

class BhushanScienceApp extends StatefulWidget {
  const BhushanScienceApp({super.key});
  @override
  State<BhushanScienceApp> createState() => _BhushanScienceAppState();
}

class _BhushanScienceAppState extends State<BhushanScienceApp> {
  String language = 'Hinglish';
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Bhushan Science',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: _accent, brightness: Brightness.dark),
          scaffoldBackgroundColor: _bg,
          useMaterial3: true,
        ),
        home: AppShell(
          language: language,
          onLanguageChanged: (value) => setState(() => language = value),
        ),
      );
}

class AppShell extends StatefulWidget {
  final String language;
  final ValueChanged<String> onLanguageChanged;
  const AppShell({super.key, required this.language, required this.onLanguageChanged});
  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int index = 0;
  @override
  Widget build(BuildContext context) {
    final pages = [
      HomePage(language: widget.language),
      LearningPage(),
      PracticePage(),
      FocusPage(),
      AdminSettingsPage(language: widget.language, onLanguageChanged: widget.onLanguageChanged),
    ];
    return Scaffold(
      body: SafeArea(child: pages[index]),
      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF121A2D),
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.menu_book), label: 'Learn'),
          NavigationDestination(icon: Icon(Icons.quiz), label: 'Practice'),
          NavigationDestination(icon: Icon(Icons.timer), label: 'Focus'),
          NavigationDestination(icon: Icon(Icons.admin_panel_settings), label: 'Admin'),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  final String language;
  const HomePage({super.key, required this.language});
  @override
  Widget build(BuildContext context) {
    final hinglish = language == 'Hinglish';
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Row(children: [
          CircleAvatar(backgroundColor: Color(0xFF282F59), child: Icon(Icons.school, color: _accent)),
          SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('BHUSHAN SCIENCE', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
            Text('Nursing learning companion', style: TextStyle(color: Colors.white60)),
          ])),
          Icon(Icons.notifications_none),
        ]),
        const SizedBox(height: 22),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [Color(0xFF343B78), Color(0xFF20294A)]),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(hinglish ? 'Padhai smart karo ✨' : 'Learn smarter ✨',
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(hinglish
                ? 'Concept samjho, practice karo—ratta maarne ki zaroorat nahi.'
                : 'Build concept clarity with structured lessons and practice.',
                style: const TextStyle(color: Colors.white70)),
          ]),
        ),
        const SizedBox(height: 20),
        const Text('Learning tracks', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        const Wrap(spacing: 12, runSpacing: 12, children: [
          HomeTile(icon: Icons.medical_services, title: 'BSc Nursing', sub: 'Semesters 1–8'),
          HomeTile(icon: Icons.health_and_safety, title: 'GNM Nursing', sub: 'Years 1–3'),
          HomeTile(icon: Icons.library_books, title: 'Syllabus map', sub: 'Subjects & chapters'),
          HomeTile(icon: Icons.auto_awesome, title: 'Smart revision', sub: 'Review concepts'),
        ]),
        const SizedBox(height: 18),
        Card(color: _panel, child: ListTile(
          leading: const Icon(Icons.support_agent, color: _accent),
          title: Text(hinglish ? 'AI Study Support' : 'AI Study Support'),
          subtitle: Text(hinglish ? 'Doubt bhejo—AI connection configure hona baaki hai.' : 'AI service connection is awaiting configuration.'),
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SupportPage(language: language))),
        )),
        const SizedBox(height: 12),
        Text(hinglish ? 'Study tip: pehle khud recall karo, phir notes check karo.' : 'Study tip: recall first, then check your notes.',
            style: const TextStyle(color: Colors.white60)),
      ],
    );
  }
}

class HomeTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String sub;
  const HomeTile({super.key, required this.icon, required this.title, required this.sub});
  @override
  Widget build(BuildContext context) => Container(
        width: MediaQuery.of(context).size.width / 2 - 27,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: _panel, borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white10)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, color: _accent, size: 28),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(sub, style: const TextStyle(color: Colors.white60, fontSize: 12)),
        ]),
      );
}

class LearningPage extends StatefulWidget {
  const LearningPage({super.key});
  @override
  State<LearningPage> createState() => _LearningPageState();
}
class _LearningPageState extends State<LearningPage> {
  String course = 'BSc Nursing';
  @override
  Widget build(BuildContext context) {
    final stages = course == 'BSc Nursing'
        ? List.generate(8, (i) => 'Semester ${i + 1}')
        : List.generate(3, (i) => 'Year ${i + 1}');
    const subjects = ['Anatomy', 'Physiology', 'Nutrition', 'Nursing Foundation', 'Microbiology'];
    return ListView(padding: const EdgeInsets.all(20), children: [
      const Text('Structured learning', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      SegmentedButton<String>(
        segments: const [ButtonSegment(value: 'BSc Nursing', label: Text('BSc Nursing')), ButtonSegment(value: 'GNM Nursing', label: Text('GNM Nursing'))],
        selected: {course},
        onSelectionChanged: (selection) => setState(() => course = selection.first),
      ),
      const SizedBox(height: 12),
      ...stages.map((stage) => Card(
        color: _panel,
        child: ExpansionTile(
          leading: const Icon(Icons.folder_open, color: _accent),
          title: Text(stage),
          subtitle: const Text('Subjects · topics · practice'),
          children: subjects.map((subject) => ListTile(
            title: Text(subject),
            subtitle: const Text('Starter content — official curriculum mapping pending'),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => LessonPage(topic: subject))),
          )).toList(),
        ),
      )),
    ]);
  }
}

class LessonPage extends StatelessWidget {
  final String topic;
  const LessonPage({super.key, required this.topic});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(topic)),
    body: ListView(padding: const EdgeInsets.all(20), children: [
      Text(topic, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
      const SizedBox(height: 10),
      const Text('Concept explanation and curriculum-backed lesson content will appear here once the content service is connected.'),
      const SizedBox(height: 18),
      const Card(color: _panel, child: ListTile(leading: Icon(Icons.notes, color: _accent), title: Text('Notes'), subtitle: Text('Lesson library connection pending'))),
    ]),
  );
}

class PracticePage extends StatefulWidget {
  const PracticePage({super.key});
  @override
  State<PracticePage> createState() => _PracticePageState();
}
class _PracticePageState extends State<PracticePage> {
  int? answer;
  bool checked = false;
  final options = ['Lungs', 'Heart', 'Kidney', 'Liver'];
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(20),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Practice & mastery', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
      const SizedBox(height: 18),
      const Text('Sample question', style: TextStyle(color: _accent)),
      const SizedBox(height: 10),
      const Text('Which organ primarily pumps blood throughout the body?', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
      const SizedBox(height: 12),
      ...options.asMap().entries.map((entry) => Card(
        color: answer == entry.key ? const Color(0xFF343B78) : _panel,
        child: ListTile(
          title: Text(entry.value),
          leading: Radio<int>(value: entry.key, groupValue: answer, onChanged: checked ? null : (value) => setState(() => answer = value)),
        ),
      )),
      if (checked) Text(answer == 1 ? 'Correct! Nice work.' : 'Correct answer: Heart. Review the concept and try again.', style: const TextStyle(fontWeight: FontWeight.bold)),
      const Spacer(),
      Row(children: [
        Expanded(child: FilledButton(onPressed: answer == null ? null : () => setState(() => checked = true), child: Text(checked ? 'Answer checked' : 'Check answer'))),
        const SizedBox(width: 10),
        Expanded(child: OutlinedButton(onPressed: () => setState(() { answer = null; checked = false; }), child: const Text('Reset'))),
      ]),
    ]),
  );
}

class FocusPage extends StatefulWidget {
  const FocusPage({super.key});
  @override
  State<FocusPage> createState() => _FocusPageState();
}
class _FocusPageState extends State<FocusPage> {
  int seconds = 1500;
  Timer? timer;
  bool running = false;
  void start() {
    if (running || seconds <= 0) return;
    setState(() => running = true);
    timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (seconds <= 1) {
        t.cancel();
        setState(() { seconds = 0; running = false; });
      } else {
        setState(() => seconds--);
      }
    });
  }
  void reset() {
    timer?.cancel();
    setState(() { seconds = 1500; running = false; });
  }
  @override
  void dispose() { timer?.cancel(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final time = '${(seconds ~/ 60).toString().padLeft(2, '0')}:${(seconds % 60).toString().padLeft(2, '0')}';
    return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      const Text('Focus session', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
      const SizedBox(height: 18),
      Container(width: 220, height: 220, decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: _accent, width: 8), color: _panel), child: Center(child: Text(time, style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold)))),
      const SizedBox(height: 24),
      Wrap(spacing: 10, children: [
        FilledButton.icon(onPressed: seconds == 0 ? reset : (running ? () { timer?.cancel(); setState(() => running = false); } : start), icon: Icon(running ? Icons.pause : Icons.play_arrow), label: Text(running ? 'Pause' : seconds == 0 ? 'Restart' : 'Start')),
        OutlinedButton.icon(onPressed: reset, icon: const Icon(Icons.refresh), label: const Text('Reset')),
      ]),
    ]));
  }
}

class AdminSettingsPage extends StatefulWidget {
  final String language;
  final ValueChanged<String> onLanguageChanged;
  const AdminSettingsPage({super.key, required this.language, required this.onLanguageChanged});
  @override
  State<AdminSettingsPage> createState() => _AdminSettingsPageState();
}
class _AdminSettingsPageState extends State<AdminSettingsPage> {
  double sessionMinutes = 25;
  double refreshMinutes = 1;
  bool enableAiSupport = true;
  bool enableFriendlyTone = true;
  String tone = 'Frank & friendly';
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [
    const Text('Admin configuration', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
    const SizedBox(height: 6),
    const Text('UI controls preview. Secure admin authentication and server-side sync must be connected before these settings can govern all users.', style: TextStyle(color: Colors.orangeAccent)),
    const SizedBox(height: 18),
    const Text('Default language', style: TextStyle(fontWeight: FontWeight.bold)),
    DropdownButton<String>(value: widget.language, isExpanded: true, items: const ['Hinglish', 'Hindi', 'English'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(), onChanged: (v) { if (v != null) widget.onLanguageChanged(v); }),
    const Divider(),
    Text('Focus duration: ${sessionMinutes.round()} minutes'),
    Slider(value: sessionMinutes, min: 5, max: 90, divisions: 17, label: '${sessionMinutes.round()} min', onChanged: (v) => setState(() => sessionMinutes = v)),
    Text('Config refresh interval: ${refreshMinutes.round()} minute(s)'),
    Slider(value: refreshMinutes, min: 1, max: 10, divisions: 9, label: '${refreshMinutes.round()} min', onChanged: (v) => setState(() => refreshMinutes = v)),
    SwitchListTile(title: const Text('AI study support'), subtitle: const Text('Switch UI option; AI provider connection still required'), value: enableAiSupport, onChanged: (v) => setState(() => enableAiSupport = v),
    SwitchListTile(title: const Text('Friendly frank voice'), value: enableFriendlyTone, onChanged: (v) => setState(() => enableFriendlyTone = v),
    const SizedBox(height: 8),
    const Text('Assistant tone', style: TextStyle(fontWeight: FontWeight.bold)),
    DropdownButton<String>(value: tone, isExpanded: true, items: const ['Frank & friendly', 'Professional', 'Playful teasing'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(), onChanged: (v) { if (v != null) setState(() => tone = v); }),
    const SizedBox(height: 12),
    FilledButton.icon(onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preview settings updated locally. Server sync is not connected yet.'))), icon: const Icon(Icons.save), label: const Text('Apply preview settings')),
  ]);
}

class SupportPage extends StatelessWidget {
  final String language;
  const SupportPage({super.key, required this.language});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Study Support')),
    body: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('AI support setup', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      Text(language == 'Hinglish'
          ? 'Abhi AI provider connect nahi hai. Backend endpoint aur securely stored API key configure hone ke baad doubts ka intelligent answer, explanation aur language matching enable hoga.'
          : 'The AI provider is not connected yet. Configure a backend endpoint and securely stored API key to enable intelligent explanations and language matching.'),
    ])),
  );
}
