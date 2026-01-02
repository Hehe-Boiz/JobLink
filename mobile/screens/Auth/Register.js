import React, { useState } from 'react';
import { View, TouchableOpacity, ScrollView } from 'react-native';
import { Text, TextInput, Button, useTheme } from 'react-native-paper';

// Import Styles
import styles from '../../styles/Auth/RegisterStyles';

const Register = ({ navigation }) => {
    // State quản lý vai trò: 'candidate' hoặc 'recruiter'
    const [role, setRole] = useState('candidate');

    // State form
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Ẩn hiện mật khẩu
    const [showPass, setShowPass] = useState(false);
    const [showConfirmPass, setShowConfirmPass] = useState(false);

    const handleRegister = () => {
        // Logic đăng ký sẽ gọi API sau này
        console.log('Registering as:', role);
        console.log('Info:', name, email);
        // Sau khi đăng ký xong -> Chuyển về Login hoặc vào Home
        navigation.navigate('Login');
    };

    return (
        <View style={styles.container}>
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 20 }}>

                {/* 1. Header: LOGO TEXT ONLY */}
                <View style={styles.headerContainer}>
                    <Text style={styles.appName}>
                        Job<Text style={styles.brandHighlight}>Link</Text>
                    </Text>
                    <Text style={styles.tagline}>
                        Create an account to find your dream job
                    </Text>
                </View>

                {/* 2. ROLE SWITCHER (Chọn vai trò) */}
                <View style={styles.toggleContainer}>
                    {/* Nút Candidate */}
                    <TouchableOpacity
                        style={[styles.toggleBtn, role === 'candidate' && styles.activeToggleBtn]}
                        onPress={() => setRole('candidate')}
                    >
                        <Text style={[styles.toggleText, role === 'candidate' && styles.activeToggleText]}>
                            Candidate
                        </Text>
                    </TouchableOpacity>

                    {/* Nút Employer */}
                    <TouchableOpacity
                        style={[styles.toggleBtn, role === 'employer' && styles.activeToggleBtn]}
                        onPress={() => setRole('employer')}
                    >
                        <Text style={[styles.toggleText, role === 'recruiter' && styles.activeToggleText]}>
                            Employer
                        </Text>
                    </TouchableOpacity>
                </View>

                {/* 3. Inputs Form */}
                <View style={styles.inputContainer}>

                    {/* Logic: Nếu là Candidate -> Nhập Tên, Nếu là Recruiter -> Nhập Tên Công ty */}
                    <TextInput
                        label={role === 'candidate' ? "Full Name" : "Company Name"}
                        value={name}
                        onChangeText={setName}
                        mode="outlined"
                        style={styles.input}
                        outlineColor="#EAEAEA"
                        activeOutlineColor="#130160"
                        theme={{ roundness: 10 }}
                        left={<TextInput.Icon icon={role === 'candidate' ? "account-outline" : "domain"} color="#AAA6B9" />}
                    />

                    <TextInput
                        label="Email"
                        value={email}
                        onChangeText={setEmail}
                        mode="outlined"
                        style={styles.input}
                        outlineColor="#EAEAEA"
                        activeOutlineColor="#130160"
                        theme={{ roundness: 10 }}
                        left={<TextInput.Icon icon="email-outline" color="#AAA6B9" />}
                    />

                    <TextInput
                        label="Password"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry={!showPass}
                        mode="outlined"
                        style={styles.input}
                        outlineColor="#EAEAEA"
                        activeOutlineColor="#130160"
                        theme={{ roundness: 10 }}
                        left={<TextInput.Icon icon="lock-outline" color="#AAA6B9" />}
                        right={<TextInput.Icon icon={showPass ? "eye-off" : "eye"} onPress={() => setShowPass(!showPass)} color="#AAA6B9" />}
                    />

                    <TextInput
                        label="Confirm Password"
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        secureTextEntry={!showConfirmPass}
                        mode="outlined"
                        style={styles.input}
                        outlineColor="#EAEAEA"
                        activeOutlineColor="#130160"
                        theme={{ roundness: 10 }}
                        left={<TextInput.Icon icon="lock-check-outline" color="#AAA6B9" />}
                        right={<TextInput.Icon icon={showConfirmPass ? "eye-off" : "eye"} onPress={() => setShowConfirmPass(!showConfirmPass)} color="#AAA6B9" />}
                    />
                </View>

                {/* 4. Action Button */}
                <Button
                    mode="contained"
                    onPress={handleRegister}
                    style={styles.registerBtn}
                    labelStyle={styles.registerBtnLabel}
                    uppercase={true}
                >
                    SIGN UP
                </Button>

                {/* 5. Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>Already have an account?</Text>
                    <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                        <Text style={styles.loginText}>Log in</Text>
                    </TouchableOpacity>
                </View>

            </ScrollView>
        </View>
    );
};

export default Register;