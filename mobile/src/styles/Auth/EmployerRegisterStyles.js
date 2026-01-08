import { StyleSheet, Dimensions } from 'react-native';

const { height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 20,
  },

  // --- SỬA PHẦN NÀY ĐỂ ĐẨY XUỐNG ---
  headerContainer: {
    alignItems: 'center',
    // Tăng khoảng cách từ đỉnh màn hình xuống (trước đây là marginVertical: 30)
    marginTop: height * 0.1, // Cách top 10% chiều cao màn hình (khoảng 80px)
    marginBottom: 40,        // Cách thanh progress bar xa hơn xíu
  },

  appName: {
    fontSize: 50,
    fontWeight: 'bold',
    color: '#130160',
    marginBottom: 5, // Thêm khoảng cách nhỏ giữa Tên app và Subtitle
  },
  brandHighlight: { color: '#FF9228' },

  // --- PROGRESS BAR ---
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 40, // Tăng khoảng cách giữa thanh tiến trình và Form nhập liệu
    paddingHorizontal: 15, // Co lại một chút cho đỡ sát lề
  },
  stepIndicator: {
    width: 32, // To hơn xíu cho dễ nhìn
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeStep: {
    backgroundColor: '#130160',
  },
  stepText: {
    fontWeight: 'bold',
    color: '#95969D',
    fontSize: 12,
  },
  activeStepText: {
    color: 'white',
  },
  stepLine: {
    flex: 1,
    height: 2,
    backgroundColor: '#F0F0F0',
    alignSelf: 'center',
    marginHorizontal: 10,
  },
  activeLine: {
    backgroundColor: '#130160',
  },

  // Form Fields
  input: {
    backgroundColor: '#FFFFFF',
    marginBottom: 20, // Tăng khoảng cách giữa các ô input cho thoáng
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#130160',
    marginBottom: 20,
  },

  // Buttons
  navButtonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 30, // Đẩy nút xuống xa form hơn
    marginBottom: 20, // Khoảng trống dưới cùng để không bị sát đáy màn hình
  },
  backBtn: {
    flex: 1,
    marginRight: 10,
    borderColor: '#95969D',
    borderWidth: 1, // Thêm viền rõ hơn
  },
  nextBtn: {
    flex: 1,
    marginLeft: 10,
    backgroundColor: '#130160',
    elevation: 3, // Đổ bóng cho nút Next nổi bật
  },
});

export default styles;