import { StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA', // Nền xám xanh hiện đại
  },

  // =================================================
  // 1. HEADER STYLES
  // =================================================
  
  // Header thường (Dùng cho PostJob, MyJobs)
  header: {
    paddingTop: 20, 
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
    elevation: 2, // Đổ bóng nhẹ cho header
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#130160',
  },
  
  // Header Xanh (Dùng cho Dashboard)
  blueHeader: {
    backgroundColor: '#2E5CFF',
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 30,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    marginBottom: 10,
  },
  headerTitleWhite: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 5,
  },
  headerSubWhite: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 15,
  },

  // =================================================
  // 2. DASHBOARD & STATS STYLES
  // =================================================
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    marginTop: -25, // Đẩy card lên đè vào header xanh
  },
  statCard: {
    width: (width - 45) / 2,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 15,
    marginBottom: 15,
    elevation: 4,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4,
  },
  statLabel: { color: '#524B6B', fontSize: 13, marginBottom: 5, fontWeight: '500' },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#130160' },
  statTrend: { fontSize: 12, fontWeight: 'bold', marginTop: 5, textAlign: 'right' },
  
  chartCard: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 15,
    borderRadius: 16,
    padding: 15,
    marginBottom: 20,
    elevation: 2,
  },
  chartTitle: { fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 15 },

  filterContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 10,
    alignSelf: 'flex-start',
    padding: 4,
  },
  filterItem: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  filterActive: { backgroundColor: '#FFFFFF' },
  filterText: { color: '#FFFFFF', fontWeight: '600', fontSize: 13 },
  filterTextActive: { color: '#2E5CFF' },

  // =================================================
  // 3. JOB CARD & LIST STYLES
  // =================================================
  jobCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    marginHorizontal: 15,
    elevation: 3,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05,
    borderLeftWidth: 4,
    borderLeftColor: '#2E5CFF',
  },
  jobTitle: { fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 5 },
  jobMetaRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  jobMetaText: { color: '#524B6B', fontSize: 13, marginLeft: 5, marginRight: 15 },
  tagSuccess: { backgroundColor: '#E8FAEF', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6, alignSelf: 'flex-start', marginTop: 5 },
  tagTextSuccess: { color: '#00C566', fontSize: 12, fontWeight: 'bold' },

  // =================================================
  // 4. FORM STYLES (DÙNG CHO POST JOB) -> Đây là phần bạn bị thiếu
  // =================================================
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#130160',
    marginBottom: 15,
    marginTop: 0,
    textTransform: 'uppercase', // Chữ in hoa tiêu đề
    letterSpacing: 0.5,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#524B6B',
    marginBottom: 8,
    marginLeft: 2,
  },
  input: {
    backgroundColor: '#FFFFFF',
    fontSize: 14,
  },
  textArea: {
    backgroundColor: '#FFFFFF',
    fontSize: 14,
    minHeight: 100, // Chiều cao tối thiểu cho ô mô tả
  },
  btnPrimary: {
    backgroundColor: '#130160',
    borderRadius: 12,
    height: 54,
    justifyContent: 'center',
    marginTop: 20,
    elevation: 5,
    shadowColor: '#130160', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3,
  }, 
  
  // =================================================
  // 5. CANDIDATE & COMMENT STYLES
  // =================================================
  candidateItem: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF',
    padding: 15, borderBottomWidth: 1, borderBottomColor: '#F5F7FA'
  },
  avatarLarge: { width: 50, height: 50, borderRadius: 25, marginRight: 15 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  
  commentBox: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 25,
    elevation: 15, // Đổ bóng đậm hơn
    shadowColor: '#000', shadowOffset: { width: 0, height: -5 }, shadowOpacity: 0.1,
    marginTop: 20,
  },
  commentInput: {
    backgroundColor: '#F9F9F9',
    borderRadius: 12,
    borderWidth: 1, borderColor: '#EAEAEA',
    padding: 15,
    height: 80, textAlignVertical: 'top',
    marginBottom: 15,
  },
  btnSend: {
    backgroundColor: '#2E5CFF',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  btnText: { color: 'white', fontWeight: 'bold', fontSize: 16 },

  // Helpers
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
});

export default styles;