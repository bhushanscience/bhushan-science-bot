import 'package:flutter_test/flutter_test.dart';
import 'package:bhushan_science_app/main.dart';

void main() {
  testWidgets('Bhushan Science opens its home screen', (tester) async {
    await tester.pumpWidget(const BhushanScienceApp());
    expect(find.text('BHUSHAN SCIENCE'), findsOneWidget);
    expect(find.text('Nursing learning companion'), findsOneWidget);
  });
}
