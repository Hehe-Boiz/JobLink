import { StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF', // Nền trắng chuẩn
        padding: 20,
        justifyContent: 'center',
    },

    // Header Text
    headerContainer: {
        alignItems: 'center',
        marginBottom: 50,
        marginTop: 60, // Đẩy xuống thấp hơn chút vì đã bỏ nền
    },

    // Đã xóa brandBackground

    appName: {
        fontSize: 48,         // Tăng kích thước từ 42 -> 48
        fontWeight: 'bold',   // Dùng 'bold' chuẩn
        color: '#130160',     // Màu Tím Than
        letterSpacing: 0.5,
        marginBottom: 5,      // Khoảng cách với slogan

        // MẸO: Đổ bóng cùng màu để làm giả hiệu ứng "Siêu Đậm"
        textShadowColor: '#130160',
        textShadowOffset: { width: 0.5, height: 0.5 }, // Bóng chệch nhẹ
        textShadowRadius: 1,
    },

    brandHighlight: {
        color: '#FF9228',     // Màu Cam
        // Cũng đổ bóng cho phần này luôn
        textShadowColor: '#FF9228',
        textShadowOffset: { width: 0.5, height: 0.5 },
        textShadowRadius: 1,
    },

    tagline: {
        fontSize: 16,        // Tăng nhẹ cỡ chữ slogan cho cân đối
        color: '#524B6B',
        fontWeight: '500',
        letterSpacing: 0.5,
    },

    // Inputs
    inputContainer: {
        marginBottom: 20,
    },
    input: {
        backgroundColor: '#FFFFFF',
        marginBottom: 15,
    },

    // Row: Remember Me & Forgot Password
    rowOptions: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 30,
    },
    checkboxContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    rememberText: {
        color: '#AAA6B9',
        fontSize: 12,
        marginLeft: 5,
    },
    forgotText: {
        color: '#130160',
        fontSize: 12,
        fontWeight: 'bold',
    },

    // Buttons
    loginBtn: {
        borderRadius: 6, // Bo góc vuông nhẹ giống hình
        height: 50,
        justifyContent: 'center',
        backgroundColor: '#130160', // Màu tím than đậm
        marginBottom: 15,
        elevation: 2,
    },
    loginBtnLabel: {
        fontSize: 14,
        fontWeight: 'bold',
        color: 'white',
    },

    googleBtn: {
        borderRadius: 6,
        height: 50,
        justifyContent: 'center',
        backgroundColor: '#E6E1FF', // Màu tím nhạt nền nút Google (hoặc xám nhạt)
        elevation: 0,
    },
    googleBtnLabel: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#0D0D26',
    },

    // Footer
    footer: {
        flexDirection: 'row',
        justifyContent: 'center',
        marginTop: 20,
    },
    footerText: {
        color: '#524B6B',
        fontSize: 12,
    },
    signupText: {
        color: '#FF9228', // Màu cam nổi bật cho link Sign Up
        fontWeight: 'bold',
        fontSize: 12,
        marginLeft: 5,
    },
});

export default styles;