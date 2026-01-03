import React, { useState } from 'react';
import { View, TouchableOpacity, Image } from 'react-native';
import { Text, TextInput, Button, Checkbox, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// Import Styles
import styles from '../../styles/Auth/LoginStyles';

const Login = ({ navigation }) => {
    const theme = useTheme();

    // States quản lý dữ liệu nhập
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [passwordVisible, setPasswordVisible] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);

    // Xử lý đăng nhập (Mock function)
    const handleLogin = () => {
        console.log('Login pressed:', email, password);
        // Logic API login sẽ viết ở đây sau
        // navigation.navigate('EmployerTabs'); // Ví dụ chuyển trang
    };

    return (
        <View style={styles.container}>

            {/* 1. Header: Welcome Back */}
            <View style={styles.headerContainer}>

                {/* Tên Thương hiệu (Nằm đè lên trên nền nhờ zIndex) */}
                <Text style={styles.appName}>
                    Job<Text style={styles.brandHighlight}>Link</Text>
                </Text>
                
                {/* Slogan */}
                <Text style={styles.tagline}>
                    Find your dream job today 🚀
                </Text>
            </View>

            {/* 2. Inputs Form */}
            <View style={styles.inputContainer}>
                <TextInput
                    label="Email"
                    value={email}
                    onChangeText={setEmail}
                    mode="outlined"
                    style={styles.input}
                    outlineColor="#EAEAEA" // Viền nhạt khi không focus
                    activeOutlineColor="#130160" // Viền đậm khi focus
                    theme={{ roundness: 10 }} // Độ bo góc
                    left={<TextInput.Icon icon="email-outline" color="#AAA6B9" />}
                />

                <TextInput
                    label="Password"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry={!passwordVisible} // Ẩn hiện pass
                    mode="outlined"
                    style={styles.input}
                    outlineColor="#EAEAEA"
                    activeOutlineColor="#130160"
                    theme={{ roundness: 10 }}
                    left={<TextInput.Icon icon="lock-outline" color="#AAA6B9" />}
                    right={
                        <TextInput.Icon
                            icon={passwordVisible ? "eye-off" : "eye"}
                            onPress={() => setPasswordVisible(!passwordVisible)}
                            color="#AAA6B9"
                        />
                    }
                />
            </View>

            {/* 3. Options: Remember Me & Forgot Password */}
            <View style={styles.rowOptions}>
                <TouchableOpacity
                    style={styles.checkboxContainer}
                    onPress={() => setRememberMe(!rememberMe)}
                >
                    {/* Custom Checkbox màu tím */}
                    <Checkbox.Android
                        status={rememberMe ? 'checked' : 'unchecked'}
                        onPress={() => setRememberMe(!rememberMe)}
                        color="#130160"
                        uncheckedColor="#AAA6B9"
                    />
                    <Text style={styles.rememberText}>Remember me</Text>
                </TouchableOpacity>

                <TouchableOpacity onPress={() => console.log('Forgot Password Pressed')}>
                    <Text style={styles.forgotText}>Forgot Password ?</Text>
                </TouchableOpacity>
            </View>

            {/* 4. Action Buttons */}
            <Button
                mode="contained"
                onPress={handleLogin}
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

            {/* 5. Footer: Sign Up Link */}
            <View style={styles.footer}>
                <Text style={styles.footerText}>You don't have an account yet?</Text>
                <TouchableOpacity onPress={() => navigation.navigate('Register')}>
                    <Text style={styles.signupText}>Sign up</Text>
                </TouchableOpacity>
            </View>

        </View>
    );
};

export default Login;