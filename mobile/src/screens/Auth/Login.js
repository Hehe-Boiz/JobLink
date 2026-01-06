import React, { useState, useContext } from 'react';
import { View, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { Text, TextInput, Button, Checkbox, HelperText, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from "@react-native-async-storage/async-storage";

// 1. Import Styles & API & Context
import styles from '../../styles/Auth/LoginStyles';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import { MyUserContext } from '../../utils/contexts/MyContext';

const Login = ({ route }) => {
    const navigation = useNavigation();
    const theme = useTheme();

    // Lấy dispatch từ Context để cập nhật user toàn cục
    const [, dispatch] = useContext(MyUserContext);

    // Cấu hình Input
    const info = [
        {
            title: "Tên đăng nhập",
            field: "username",
            icon: "account-outline"
        },
        {
            title: "Mật khẩu",
            field: "password",
            icon: "lock-outline",
            secure: true
        }
    ];

    // State
    const [user, setUser] = useState({});
    const [loading, setLoading] = useState(false);
    const [showPass, setShowPass] = useState({});
    const [rememberMe, setRememberMe] = useState(false);
    const [err, setErr] = useState(false); // State lỗi để hiển thị HelperText

    // Hàm Validate
    const validate = () => {
        if (!user.username || !user.password) {
            setErr(true);
            return false;
        }
        setErr(false);
        return true;
    }

    // --- HÀM LOGIN CHÍNH (LOGIC CỦA BẠN) ---
    const login = async () => {
        if (validate()) {
            try {
                setLoading(true);
                console.log(user);
                // 1. Gọi API lấy Token (OAuth2)
                let res = await Apis.post(endpoints['login'], {
                    ...user,
                    'client_id': '6ggfozYm0GXBwradb487j7KQed12z5pm76q8QFiD',
                    'client_secret': '3Ep4P7pK9d2LO0ksGSimeTNktjapz2lAl2pF0vhjZKkdxWRJVDSO2Us6oZSyzSCZRr4NhU2POoIpfontO3B2yWjjnYvCF73aEvFlVYArrp42OEZcOUJdJdSlf6LJhbAa',
                    'grant_type': 'password'
                });
                // 2. Lưu Token vào máy
                await AsyncStorage.setItem('token', res.data.access_token);

                // 3. Lấy thông tin User hiện tại (Current User)
                setTimeout(async () => {
                    console.log(res.data.access_token)
                    let userRes = await authApis(res.data.access_token).get(endpoints['current_user']);

                    // 4. Lưu User vào Context (Redux/Context API)
                    dispatch({
                        "type": "login",
                        "payload": userRes.data
                    });

                    // 5. Điều hướng thông minh
                    // Nếu có trang kế tiếp (do bị chặn login) thì quay lại đó
                    const next = route.params?.next;
                    if (next) {
                        navigation.navigate(next);
                    } else {
                        // Nếu không, chuyển hướng theo vai trò (Role-based Navigation)
                        const role = userRes.data.role;
                        console.log(role); 
                        if (role === 'EMPLOYER') {
                            navigation.navigate('EmployerMain'); // Vào màn hình NTD
                        } else {
                            navigation.navigate('CandidateMain'); // Vào màn hình Ứng viên
                        }
                    }
                }, 100);

            } catch (ex) {
                console.error(ex);
                let msg = "Tên đăng nhập hoặc mật khẩu không đúng!";
                if (ex.message === "Network Error") msg = "Lỗi kết nối server!";
                Alert.alert("Đăng nhập thất bại", msg);
            } finally {
                setLoading(false);
            }
        }
    }

    const toggleShow = (field) => {
        setShowPass(prev => ({ ...prev, [field]: !prev[field] }));
    }

    return (
        <View style={styles.container}>
            {/* Header JobLink */}
            <View style={styles.headerContainer}>
                <Text style={styles.appName}>
                    Job<Text style={styles.brandHighlight}>Link</Text>
                </Text>
                <Text style={styles.tagline}>
                    Find your dream job today 🚀
                </Text>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>

                {/* Thông báo lỗi */}
                <HelperText type="error" visible={err} style={{ textAlign: 'center' }}>
                    Vui lòng nhập đầy đủ thông tin!
                </HelperText>

                {/* Form Inputs */}
                <View style={styles.inputContainer}>
                    {info.map(i => (
                        <TextInput
                            key={i.field}
                            style={styles.input}
                            value={user[i.field]}
                            onChangeText={(t) => {
                                setUser({ ...user, [i.field]: t });
                                if (err) setErr(false);
                            }}
                            label={i.title}
                            mode="outlined"
                            outlineColor="#EAEAEA"
                            activeOutlineColor="#130160"
                            theme={{ roundness: 10 }}

                            secureTextEntry={i.secure ? !showPass[i.field] : false}
                            left={<TextInput.Icon icon={i.icon} color="#AAA6B9" />}
                            right={
                                i.secure ?
                                    <TextInput.Icon
                                        icon={showPass[i.field] ? "eye-off" : "eye"}
                                        onPress={() => toggleShow(i.field)}
                                        color="#AAA6B9"
                                    /> : null
                            }
                        />
                    ))}
                </View>

                {/* Options: Remember Me */}
                <View style={styles.rowOptions}>
                    <TouchableOpacity
                        style={styles.checkboxContainer}
                        onPress={() => setRememberMe(!rememberMe)}
                    >
                        <Checkbox.Android
                            status={rememberMe ? 'checked' : 'unchecked'}
                            onPress={() => setRememberMe(!rememberMe)}
                            color="#130160"
                            uncheckedColor="#AAA6B9"
                        />
                        <Text style={styles.rememberText}>Remember me</Text>
                    </TouchableOpacity>

                    <TouchableOpacity onPress={() => console.log('Forgot Password')}>
                        <Text style={styles.forgotText}>Forgot Password ?</Text>
                    </TouchableOpacity>
                </View>

                {/* Login Button */}
                <Button
                    loading={loading}
                    disabled={loading}
                    mode="contained"
                    onPress={login}
                    style={styles.loginBtn}
                    labelStyle={styles.loginBtnLabel}
                    uppercase={true}
                >
                    LOGIN
                </Button>

            <Button
                mode="contained"
                onPress={() => console.log('Google Login')}
                style={styles.googleBtn}
                labelStyle={styles.googleBtnLabel}
                icon={({ size, color }) => (
                        <MaterialCommunityIcons name="google" size={20} color="#EA4335" />
                )}
            >
                SIGN IN WITH GOOGLE
            </Button>

                {/* Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>You don't have an account yet?</Text>
                    <TouchableOpacity onPress={() => navigation.navigate('CandidateRegister')}>
                        <Text style={styles.signupText}>Sign up</Text>
                    </TouchableOpacity>
                </View>

            </ScrollView>
        </View>
    );
};

export default Login;