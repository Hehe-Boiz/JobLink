import React, {useState, useContext} from 'react';
import {View, TouchableOpacity, ScrollView, Alert} from 'react-native';
import {Text, TextInput, Button, Checkbox, HelperText, useTheme} from 'react-native-paper';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import {useNavigation} from '@react-navigation/native';
import AsyncStorage from "@react-native-async-storage/async-storage";

import styles from '../../styles/Auth/LoginStyles';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import { MyUserContext } from '../../utils/contexts/MyContext';
import { useEmployer } from '../../hooks/useEmployer';
import { useDialog } from '../../hooks/useDialog';
import { useEffect } from 'react';
import {
    GoogleSignin,
    statusCodes,
    isErrorWithCode
} from '@react-native-google-signin/google-signin';
import { CLIENT_ID, CLIENT_SECRET } from '@env';//

const Login = ({route}) => {
    const navigation = useNavigation();
    const theme = useTheme();
    const {profile, loadEmployerProfile} = useEmployer();
    const [, dispatch] = useContext(MyUserContext);
    const { showDialog } = useDialog();
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
    const [err, setErr] = useState(false);
    useEffect(() => {
        GoogleSignin.configure({
            webClientId: '665244573266-77l5gm6jcvsimql5jntqc6g102geoh09.apps.googleusercontent.com',
            offlineAccess: true, 
            forceCodeForRefreshToken: true,
        });
    }, []);
    const loginWithBackend = async (googleToken) => {
        setLoading(true);
        try {
            let res = await Apis.post(endpoints['login_google'], {
                token: googleToken
            });

            console.log("Backend Response:", res.data);

            const accessToken = res.data.access_token;
            await AsyncStorage.setItem('token', accessToken);

            let userRes = await authApis(accessToken).get(endpoints['current_user']);

            dispatch({ "type": "login", "payload": userRes.data });

            if (userRes.data.role === 'EMPLOYER') {
                let res_emp = await loadEmployerProfile(accessToken);
                if (res_emp && res_emp.is_verified === false) {
                    showDialog({
                        type: 'error',
                        title: 'Chưa được duyệt',
                        content: 'Tài khoản Nhà tuyển dụng của bạn chưa được Admin phê duyệt. Vui lòng liên hệ quản trị viên để được kích hoạt.',
                        confirmText: 'ĐÃ HIỂU',
                    });
                    try {
                        await Apis.post(endpoints['logout'], {
                            'token': res.data.access_token,
                            'client_id': CLIENT_ID,
                            'client_secret': CLIENT_SECRET,
                        });
                    }
                    catch (ex) {
                        showDialog({
                            type: 'error',
                            title: 'Lỗi',
                            content: 'Có lỗi xảy ra. Vui lòng thử lại sau.',
                            confirmText: 'ĐÃ HIỂU',
                        });
                    }
                    return;
                }
                navigation.navigate('EmployerMain');
            } else {
                navigation.navigate('CandidateMain');
            }

        } catch (error) {
            console.error(error);
            Alert.alert("Lỗi Server", "Xác thực thất bại.");
        } finally {
            setLoading(false);
        }
    };
    const signInWithGoogle = async () => {
        try {
            setLoading(true);
            await GoogleSignin.hasPlayServices();
            const userInfo = await GoogleSignin.signIn();
            const token = userInfo.data?.idToken || userInfo.idToken;

            console.log("Google ID Token:", token);

            if (token) {
                loginWithBackend(token);
            } else {
                Alert.alert("Lỗi", "Không lấy được Token từ Google");
            }

        } catch (error) {
            console.log("Google Signin Error:", error);
            if (isErrorWithCode(error, statusCodes.SIGN_IN_CANCELLED)) {
                console.log("Người dùng hủy đăng nhập");
            } else if (isErrorWithCode(error, statusCodes.IN_PROGRESS)) {
                console.log("Đang đăng nhập rồi");
            } else if (isErrorWithCode(error, statusCodes.PLAY_SERVICES_NOT_AVAILABLE)) {
                Alert.alert("Lỗi", "Máy không có Google Play Services");
            } else {
                Alert.alert("Lỗi Đăng nhập", error.message);
            }
        }
        finally {
            setLoading(false);
        }
    };
    
    const validate = () => {
        if (!user.username || !user.password) {
            setErr(true);
            return false;
        }
        setErr(false);
        return true;
    }
    const login = async () => {
        if (validate()) {
            try {
                console.log(CLIENT_ID);
                console.log(CLIENT_SECRET);
                setLoading(true);
                console.log(user);
                let res = await Apis.post(endpoints['login'], {
                    ...user,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'grant_type': 'password'
                });

                setTimeout(async () => {
                    console.log(res.data.access_token)
                    let userRes = await authApis(res.data.access_token).get(endpoints['current_user']);
                    console.log(userRes.data);
                    dispatch({
                        "type": "login",
                        "payload": userRes.data
                    });
                    if (userRes.data.role === 'EMPLOYER') {
                        console.log("Đang tải hồ sơ công ty...");
                        let res_emp = await loadEmployerProfile(res.data.access_token);
                        if (res_emp && res_emp.is_verified === false) {
                            showDialog({
                                type: 'error',
                                title: 'Chưa được duyệt',
                                content: 'Tài khoản Nhà tuyển dụng của bạn chưa được Admin phê duyệt. Vui lòng liên hệ quản trị viên để được kích hoạt.',
                                confirmText: 'ĐÃ HIỂU',
                            });
                            try {
                                await Apis.post(endpoints['logout'], {
                                    'token': res.data.access_token,
                                    'client_id': CLIENT_ID,
                                    'client_secret': CLIENT_SECRET,
                                });
                            }
                            catch (ex) {
                                showDialog({
                                    type: 'error',
                                    title: 'Lỗi',
                                    content: 'Có lỗi xảy ra. Vui lòng thử lại sau.',
                                    confirmText: 'ĐÃ HIỂU',
                                });
                            }
                            return;
                        }
                        await AsyncStorage.setItem('token', res.data.access_token);
                        const next = route.params?.next;
                        if (next) {
                            navigation.navigate(next);
                        } else {
                            const role = userRes.data.role;
                            console.log(role);
                            if (role === 'EMPLOYER') {
                                navigation.navigate('EmployerMain');

                            } else {
                                navigation.navigate('CandidateMain');
                            }
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
        setShowPass(prev => ({...prev, [field]: !prev[field]}));
    }

    return (
        <View style={styles.container}>

            <View style={styles.headerContainer}>
                <Text style={styles.appName}>
                    Job<Text style={styles.brandHighlight}>Link</Text>
                </Text>
                <Text style={styles.tagline}>
                    Find your dream job today 🚀
                </Text>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>

                <HelperText type="error" visible={err} style={{textAlign: 'center'}}>
                    Vui lòng nhập đầy đủ thông tin!
                </HelperText>

                <View style={styles.inputContainer}>
                    {info.map(i => (
                        <TextInput
                            key={i.field}
                            style={styles.input}
                            value={user[i.field]}
                            onChangeText={(t) => {
                                setUser({...user, [i.field]: t});
                                if (err) setErr(false);
                            }}
                            label={i.title}
                            mode="outlined"
                            outlineColor="#EAEAEA"
                            activeOutlineColor="#130160"
                            theme={{roundness: 10}}

                            secureTextEntry={i.secure ? !showPass[i.field] : false}
                            left={<TextInput.Icon icon={i.icon} color="#AAA6B9"/>}
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
                    onPress={signInWithGoogle}
                    disabled={loading}
                    style={styles.googleBtn}
                    labelStyle={styles.googleBtnLabel}
                    icon={({size, color}) => (
                        <MaterialCommunityIcons name="google" size={20} color="#EA4335"/>
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