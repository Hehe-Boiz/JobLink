import React, { useState } from 'react';
import { View, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, Button, HelperText } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import styles from '../../styles/Auth/EmployerRegisterStyles';
import Apis, { endpoints } from "../../utils/Apis";
import { useDialog } from '../../hooks/useDialog';

const EmployerRegister = () => {
    const navigation = useNavigation();
    const { showDialog } = useDialog();

    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // --- 1. CẤU HÌNH INPUT (Giống CandidateRegister nhưng có thêm thuộc tính 'step') ---
    const info = [
        // BƯỚC 1: Thông tin cá nhân
        {
            title: "Họ (Last Name)",
            field: "last_name",
            icon: "account-outline",
            step: 1
        },
        {
            title: "Tên (First Name)",
            field: "first_name",
            icon: "account-outline",
            step: 1
        },
        {
            title: "Email đăng nhập",
            field: "email",
            icon: "email-outline",
            step: 1,
            keyboardType: "email-address"
        },
        {
            title: "Số điện thoại",
            field: "phone",
            icon: "phone-outline",
            step: 1,
            keyboardType: "phone-pad"
        },

        // BƯỚC 2: Thông tin công ty
        {
            title: "Tên công ty",
            field: "company_name",
            icon: "domain",
            step: 2
        },
        {
            title: "Mã số thuế",
            field: "tax_code",
            icon: "card-account-details-outline",
            step: 2
        },
        {
            title: "Website",
            field: "website",
            icon: "web",
            step: 2,
            autoCapitalize: "none"
        },

        // BƯỚC 3: Mật khẩu
        {
            title: "Mật khẩu",
            field: "password",
            icon: "lock-outline",
            step: 3,
            secure: true
        },
        {
            title: "Nhập lại mật khẩu",
            field: "confirm",
            icon: "lock-check-outline",
            step: 3,
            secure: true
        }
    ];

    // State quản lý dữ liệu form & hiển thị pass
    const [formData, setFormData] = useState({});
    const [showPass, setShowPass] = useState({});
    const [err, setErr] = useState(false); // Dùng để highlight lỗi confirm pass

    const updateData = (key, value) => {
        setFormData({ ...formData, [key]: value });
        if (err) setErr(false); // Reset lỗi khi gõ lại
    };

    const toggleShow = (field) => {
        setShowPass(prev => ({ ...prev, [field]: !prev[field] }));
    };

    // --- HÀM RENDER INPUT ĐỘNG THEO BƯỚC ---
    const renderInputsForStep = (currentStep) => {
        // Lọc ra các field thuộc bước hiện tại
        const fields = info.filter(item => item.step === currentStep);

        return fields.map((item) => {
            // Logic check lỗi cho password
            const isErrorField = err && (item.field === 'password' || item.field === 'confirm');

            return (
                <View key={item.field} style={{ marginBottom: 10 }}>
                    <TextInput
                        label={item.title}
                        value={formData[item.field] || ''}
                        onChangeText={(t) => updateData(item.field, t)}
                        mode="outlined"
                        style={styles.input}
                        outlineColor="#EAEAEA"
                        activeOutlineColor={isErrorField ? "red" : "#130160"}
                        theme={{ roundness: 10 }}
                        keyboardType={item.keyboardType || 'default'}
                        autoCapitalize={item.autoCapitalize || 'sentences'}

                        secureTextEntry={item.secure ? !showPass[item.field] : false}
                        left={<TextInput.Icon icon={item.icon} color={isErrorField ? "red" : "#AAA6B9"} />}
                        right={
                            item.secure ?
                                <TextInput.Icon
                                    icon={showPass[item.field] ? "eye-off" : "eye"}
                                    onPress={() => toggleShow(item.field)}
                                    color={isErrorField ? "red" : "#AAA6B9"}
                                /> : null
                        }
                    />
                </View>
            );
        });
    };

    // --- LOGIC NAVIGATION & VALIDATE TỪNG BƯỚC ---
    const handleNext = () => {
        if (step === 1) {
            if (!formData.first_name || !formData.last_name || !formData.email || !formData.phone) {
                showDialog({ type: 'warning', title: 'Thiếu thông tin', content: 'Vui lòng điền đầy đủ thông tin cá nhân.' });
                return;
            }
            setStep(2);
        } else if (step === 2) {
            if (!formData.company_name) {
                showDialog({ type: 'warning', title: 'Thiếu thông tin', content: 'Vui lòng nhập tên công ty.' });
                return;
            }
            setStep(3);
        } else if (step === 3) {
            handleRegister();
        }
    };

    const handleBack = () => {
        if (step > 1) setStep(step - 1);
        else navigation.goBack();
    };

    // --- LOGIC GỌI API ---
    const handleRegister = async () => {
        if (formData.password !== formData.confirm) {
            setErr(true);
            showDialog({ type: 'error', title: 'Lỗi', content: 'Mật khẩu xác nhận không khớp!' });
            return;
        }

        setLoading(true);
        try {
            let form = new FormData();

            // Lấy tất cả key trong info (trừ confirm) để append vào form
            info.forEach(item => {
                if (item.field !== 'confirm' && formData[item.field]) {
                    form.append(item.field, formData[item.field]);
                }
            });
            form.append('role', 'EMPLOYER');

            console.info("Sending Data:", formData);

            const res = await Apis.post(endpoints['register_employer'], form, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            if (res.status === 201) {
                showDialog({
                    type: 'success',
                    title: 'Đăng ký thành công',
                    content: 'Tài khoản của bạn đã được tạo. Vui lòng chờ Admin phê duyệt.',
                    confirmText: 'VỀ ĐĂNG NHẬP',
                    onConfirm: () => navigation.navigate('Login')
                });
            }

        } catch (ex) {
            let message = "Đăng ký thất bại. Vui lòng thử lại.";
            if (ex.response && ex.response.data) {
                const errorData = ex.response.data;
                const fieldMap = {
                    "email": "Email", "username": "Tên đăng nhập", "password": "Mật khẩu",
                    "first_name": "Tên", "last_name": "Họ", "phone": "Số điện thoại",
                    "company_name": "Tên công ty", "tax_code": "Mã số thuế", "non_field_errors": "Lỗi"
                };

                if (typeof errorData === 'object') {
                    message = "";
                    for (let key in errorData) {
                        let vnField = fieldMap[key] || key;
                        let errContent = Array.isArray(errorData[key]) ? errorData[key][0] : errorData[key];
                        message += `${vnField}: ${errContent}\n`;
                    }
                }
            }
            showDialog({ type: 'error', title: 'Lỗi', content: message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
            <View style={styles.container}>
                <ScrollView contentContainerStyle={{ paddingBottom: 30 }} showsVerticalScrollIndicator={false}>

                    <View style={styles.headerContainer}>
                        <Text style={styles.appName}>Job<Text style={styles.brandHighlight}>Link</Text></Text>
                        <Text style={styles.tagline}>Đăng ký nhà tuyển dụng</Text>
                    </View>

                    {/* Progress Bar */}
                    <View style={styles.progressContainer}>
                        {[1, 2, 3].map(s => (
                            <React.Fragment key={s}>
                                <View style={[styles.stepIndicator, step >= s && styles.activeStep]}>
                                    <Text style={[styles.stepText, step >= s && styles.activeStepText]}>{s}</Text>
                                </View>
                                {s < 3 && <View style={[styles.stepLine, step > s && styles.activeLine]} />}
                            </React.Fragment>
                        ))}
                    </View>

                    {/* FORM CONTAINER: Gọi hàm render động */}
                    <View style={styles.formContainer}>
                        <Text style={styles.sectionTitle}>
                            {step === 1 ? "Thông tin người liên hệ" : step === 2 ? "Thông tin doanh nghiệp" : "Thiết lập bảo mật"}
                        </Text>

                        {step === 3 && (
                            <HelperText type="error" visible={err}>Mật khẩu KHÔNG khớp!</HelperText>
                        )}

                        {/* --- RENDER CÁC Ô NHẬP TẠI ĐÂY --- */}
                        {renderInputsForStep(step)}
                    </View>

                    {/* Buttons */}
                    <View style={styles.navButtonContainer}>
                        <Button
                            mode="outlined" onPress={handleBack}
                            style={styles.backBtn} textColor="#524B6B" disabled={loading}
                        >
                            {step === 1 ? "Hủy" : "Quay lại"}
                        </Button>

                        <Button
                            mode="contained" onPress={handleNext}
                            style={styles.nextBtn} loading={loading} disabled={loading}
                        >
                            {step === 3 ? "Đăng Ký" : "Tiếp theo"}
                        </Button>
                    </View>

                </ScrollView>
            </View>
        </KeyboardAvoidingView>
    );
};

export default EmployerRegister;