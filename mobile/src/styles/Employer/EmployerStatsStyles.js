import { StyleSheet } from 'react-native';

const EmployerStatsStyles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 28 },
  row: { flexDirection: 'row', gap: 12 },
  card: { borderRadius: 16 },
  title: { fontWeight: '900' },
  chipRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', marginTop: 10 },
  spacer12: { height: 12 },
  spacer16: { height: 16 },
  barRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 },
  miniLabel: { opacity: 0.7 },
});

export default EmployerStatsStyles;
