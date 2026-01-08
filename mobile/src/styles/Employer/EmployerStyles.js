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
  // ... (Các styles cũ)

  // --- CANDIDATE DETAIL STYLES (MỚI) ---
  // ... (Các style cũ giữ nguyên)

  // --- THÊM MỚI ĐOẠN NÀY ---
  
  // 1. Card chứa thông tin Profile (Màu trắng, nổi lên trên)
  profileCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginTop: 40, // Đẩy xuống để chừa chỗ cho Avatar nổi lên
    marginBottom: 20,
    elevation: 4, // Đổ bóng Android
    shadowColor: '#000', // Đổ bóng iOS
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    position: 'relative', // Quan trọng để định vị
  },

  // 2. Avatar (Tròn, có viền trắng, nổi lên)
  profileAvatar: {
    width: 100,  
    height: 100,  
    borderRadius: 50,
    borderWidth: 4,
    borderColor: '#F5F7FA', // Màu trùng với nền màn hình để tạo hiệu ứng cắt
    marginTop: -70, // Kéo ngược lên trên để "nổi" (Floating)
    alignSelf: 'center', // Căn giữa
    backgroundColor: '#FFF', // Nền trắng dự phòng
  },

  // 3. Tên và Chức vụ
  profileName: { 
    fontSize: 22, 
    fontWeight: 'bold', 
    color: '#130160',
    textAlign: 'center',
    marginTop: 10 
  },
  profileJob: { 
    fontSize: 14, 
    color: '#524B6B', 
    textAlign: 'center',
    marginTop: 4 
  },

  // 4. Các Card thông tin khác
  sectionHeader: {
    fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 12, marginLeft: 5
  },
  infoCard: {
    backgroundColor: 'white', borderRadius: 16, padding: 20, marginBottom: 20,
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.05
  },
  
  // 5. Icon trong phần Kinh nghiệm/Học vấn
  iconBox: {
    width: 44, height: 44, borderRadius: 12, backgroundColor: '#F5F7FA',
    justifyContent: 'center', alignItems: 'center'
  },
  infoLabel: { fontSize: 14, fontWeight: 'bold', color: '#130160' },
  infoValue: { fontSize: 14, color: '#524B6B', marginTop: 2 },
  infoSub: { fontSize: 12, color: '#95969D', marginTop: 2, fontStyle: 'italic' },

  // 6. Card CV
  cvCard: {
    backgroundColor: 'white', borderRadius: 16, padding: 15, marginBottom: 25,
    flexDirection: 'row', alignItems: 'center',
    borderWidth: 1, borderColor: '#EAEAEA',
    elevation: 2
  },
  cvIconContainer: {
    width: 50, height: 50, borderRadius: 10, backgroundColor: '#FFF4E5',
    justifyContent: 'center', alignItems: 'center'
  },
  cvName: { fontSize: 15, fontWeight: 'bold', color: '#130160' },
  cvSize: { fontSize: 12, color: '#FF9228', marginTop: 2 },

  // 7. Input Comment
  commentInputNew: {
    backgroundColor: '#F9F9F9', borderRadius: 12,
    borderWidth: 1, borderColor: '#EAEAEA',
    padding: 15, height: 100, textAlignVertical: 'top',
    marginBottom: 20, fontSize: 14
  },
  btnSave: {
    backgroundColor: '#130160', borderRadius: 12, paddingVertical: 14, alignItems: 'center',
    elevation: 3
  },
  btnSaveText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  // ... (Các style cũ)

  // --- EMPLOYER PROFILE STYLES (MỚI) ---
  
  // 1. Ảnh bìa & Header
  profileBanner: {
    height: 140,
    width: '100%',
    backgroundColor: '#130160', // Màu nền nếu không có ảnh
  },
  profileHeaderContainer: {
    alignItems: 'center',
    marginTop: -50, // Kéo logo đè lên ảnh bìa
    marginBottom: 20,
  },
  employerLogo: {
    width: 100, height: 100, 
    borderRadius: 16, // Logo công ty thường hình vuông bo góc
    borderWidth: 4, borderColor: '#F5F7FA',
    backgroundColor: 'white',
  },
  companyName: {
    fontSize: 22, fontWeight: 'bold', color: '#130160',
    marginTop: 10, textAlign: 'center',
  },
  companyEmail: {
    fontSize: 14, color: '#524B6B', marginBottom: 5,
  },
  verifyBadge: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#E8FAEF', paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 20, marginTop: 5
  },
  verifyText: { color: '#00C566', fontWeight: 'bold', fontSize: 12, marginLeft: 4 },

  // 2. Thống kê nhanh (Stats Row)
  statsRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    backgroundColor: 'white', marginHorizontal: 20, borderRadius: 16,
    padding: 20, marginBottom: 20,
    elevation: 4, shadowColor: '#000', shadowOffset: {width:0, height:2}, shadowOpacity:0.1
  },
  statItem: { alignItems: 'center', flex: 1 },
  statNumber: { fontSize: 18, fontWeight: 'bold', color: '#130160' },
  statLabel: { fontSize: 12, color: '#95969D', marginTop: 4 },
  verticalDivider: { width: 1, backgroundColor: '#EAEAEA', height: '80%' },

  // 3. Menu Item
  menuSection: {
    backgroundColor: 'white', marginHorizontal: 20, borderRadius: 16,
    paddingVertical: 10, marginBottom: 20,
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.05
  },
  menuItem: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingVertical: 15, paddingHorizontal: 20,
    borderBottomWidth: 1, borderBottomColor: '#F9F9F9'
  },
  menuIconBox: {
    width: 40, height: 40, borderRadius: 10, backgroundColor: '#F5F7FA',
    justifyContent: 'center', alignItems: 'center', marginRight: 15
  },
  menuText: { fontSize: 15, fontWeight: '600', color: '#130160' },
  
  // 4. Logout Button
  logoutBtn: {
    marginHorizontal: 20, marginBottom: 40,
    backgroundColor: '#FFECEC', borderRadius: 12,
    paddingVertical: 15, flexDirection: 'row', justifyContent: 'center', alignItems: 'center'
  },
  logoutText: { color: '#FF4D4D', fontWeight: 'bold', fontSize: 16, marginLeft: 8 },
  // ... Các style cũ

  // --- EDIT PROFILE STYLES (MỚI) ---
  editAvatarContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  editAvatar: {
    width: 120, height: 120,
    borderRadius: 60,
    borderWidth: 4, borderColor: '#FFFFFF',
    backgroundColor: '#F5F7FA',
  },
  cameraBtn: {
    position: 'absolute',
    bottom: 0, right: '35%', // Căn chỉnh nút camera
    backgroundColor: '#130160',
    width: 36, height: 36, borderRadius: 18,
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: '#FFFFFF',
  },
  
  // Style cho Form
  formSection: {
    backgroundColor: 'white',
    padding: 20, borderRadius: 16,
    marginBottom: 20,
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.05
  },
  formTitle: {
    fontSize: 16, fontWeight: 'bold', color: '#130160',
    marginBottom: 15, borderLeftWidth: 4, borderLeftColor: '#FF9228',
    paddingLeft: 10,
  },
  // =================================================
  // 2. DASHBOARD & STATS STYLES
  // =================================================
  // --- DASHBOARD NEW STYLES ---
  // --- NEW PROFESSIONAL DASHBOARD STYLES ---
  
  // 1. Header Sang trọng
  proHeader: {
    backgroundColor: '#130160',
    paddingTop: 60, // Tăng padding top để tránh tai thỏ
    paddingBottom: 40,
    paddingHorizontal: 25,
    borderBottomLeftRadius: 35,
    borderBottomRightRadius: 35,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    // Shadow đậm tạo chiều sâu
    shadowColor: '#130160',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 15,
    zIndex: 1,
  },
  headerLeft: {
    flex: 1,
  },
  dateText: {
    color: '#FF9228', // Màu cam tạo điểm nhấn
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  welcomeText: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  notifBtn: {
    width: 45, height: 45,
    borderRadius: 15,
    backgroundColor: 'rgba(255,255,255,0.15)', // Trong suốt
    justifyContent: 'center', alignItems: 'center',
    marginRight: 15,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)'
  },
  avatarContainer: {
    padding: 2,
    backgroundColor: 'white',
    borderRadius: 25,
  },
  headerAvatar: {
    width: 46, height: 46,
    borderRadius: 23,
  },

  // 2. Stats Row (Chỉ còn 2 thẻ to)
  statsContainerPro: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginTop: 20, // Đẩy lên đè vào Header
    zIndex: 2,
  },
  statCardPro: {
    width: '48%',
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    // Shadow nhẹ nhàng
    elevation: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 8,
  },
  statIconBox: {
    width: 45, height: 45, borderRadius: 14,
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 12
  },
  statNumberPro: { fontSize: 28, fontWeight: 'bold', color: '#130160' },
  statLabelPro: { fontSize: 13, color: '#524B6B', marginTop: 2, fontWeight: '500' },

  // 3. Chart Section
  sectionHeaderPro: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 25, marginTop: 25, marginBottom: 15
  },
  sectionTitlePro: { fontSize: 18, fontWeight: 'bold', color: '#130160' },
  chartCardPro: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    borderRadius: 24,
    padding: 15,
    elevation: 3, shadowColor: '#000', shadowOpacity: 0.05,
    marginBottom: 20
  },
  // ... (Các style cũ giữ nguyên)

  // --- DASHBOARD UPGRADE STYLES ---
  
  // 1. Time Filter Tabs (Tuần/Tháng/Năm)
  filterTabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    marginHorizontal: 20,
    marginTop: 25,
    borderRadius: 12,
    padding: 4,
    justifyContent: 'space-between',
    elevation: 2, shadowColor: '#000', shadowOpacity: 0.05
  },
  filterTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  filterTabActive: {
    backgroundColor: '#130160', // Màu active
  },
  filterText: {
    fontWeight: '600',
    fontSize: 13,
    color: '#95969D'
  },
  filterTextActive: {
    color: 'white'
  },

  // 2. Chart Card mở rộng
  chartCardPro: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    borderRadius: 24,
    padding: 15,
    elevation: 3, shadowColor: '#000', shadowOpacity: 0.05,
    marginBottom: 20,
    alignItems: 'center' // Căn giữa chart
  },
  legendContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 10
  },
  legendItem: {
    flexDirection: 'row', alignItems: 'center', marginRight: 15, marginBottom: 5
  },
  legendDot: { width: 10, height: 10, borderRadius: 5, marginRight: 5 },
  legendText: { fontSize: 12, color: '#524B6B' },  
});

export default styles;