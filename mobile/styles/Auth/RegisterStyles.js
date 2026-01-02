import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 20,
    justifyContent: 'center',
  },
  
  // Header: Giống hệt Login
  headerContainer: {
    alignItems: 'center',
    marginBottom: 30, // Giảm chút cho đỡ chật vì form đăng ký dài hơn
    marginTop: 40,
  },
  appName: {
    fontSize: 40, // Nhỏ hơn Login xíu (50 -> 40) để tiết kiệm chỗ
    fontWeight: 'bold',
    color: '#130160',
    letterSpacing: -1,
    marginBottom: 5,
  },
  brandHighlight: {
    color: '#FF9228',
  },
  tagline: {
    fontSize: 14,
    color: '#524B6B',
    fontWeight: '500',
    textAlign: 'center',
  },

  // --- ROLE SWITCHER (Nút chọn vai trò) ---
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#F5F6FA',
    borderRadius: 12,
    padding: 4,
    marginBottom: 25,
    height: 50,
  },
  toggleBtn: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 10,
  },
  activeToggleBtn: {
    backgroundColor: '#FFFFFF', // Nút đang chọn màu trắng nổi lên
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#95969D',
  },
  activeToggleText: {
    color: '#130160', // Màu chữ tím than khi active
    fontWeight: 'bold',
  },

  // Inputs
  inputContainer: {
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#FFFFFF',
    marginBottom: 15,
  },

  // Buttons
  registerBtn: {
    borderRadius: 6,
    height: 50,
    justifyContent: 'center',
    backgroundColor: '#130160',
    marginBottom: 20,
    elevation: 2,
  },
  registerBtnLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: 'white',
  },

  // Footer
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 20,
  },
  footerText: {
    color: '#524B6B',
    fontSize: 12,
  },
  loginText: {
    color: '#FF9228',
    fontWeight: 'bold',
    fontSize: 12,
    marginLeft: 5,
  },
});

export default styles;