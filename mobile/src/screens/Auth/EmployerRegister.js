import React, { useState } from 'react';
import { View, ScrollView, Alert } from 'react-native'; // Thêm Alert
import { Text, TextInput, Button, HelperText } from 'react-native-paper';
import styles from '../../styles/Auth/EmployerRegisterStyles';
import Apis, { endpoints } from "../../utils/Apis"; // Import API

const EmployerRegister = ({ navigation }) => {
    const [step, setStep] = useState(1); // Giữ nguyên logic chuyển bước
    const [loading, setLoading] = useState(false); // State loading khi gọi API

    // 1. Dữ liệu form (Cập nhật đủ các trường backend cần)
    const [formData, setFormData] = useState({
        first_name: '', // Tên người liên hệ (Quan trọng)
        email: '',
        password: '',
        confirm: '', // Thêm confirm pass
        company_name: '',
        website: '',
        phone: '',
    });

    // Helper update state
    const updateData = (key, value) => {
        setFormData({ ...formData, [key]: value });
    };


    // 2. LOGIC ĐĂNG KÝ
    const register = async () => {
        // Validate cơ bản
        if (formData.password !== formData.confirm) {
            Alert.alert("Lỗi", "Mật khẩu xác nhận không khớp!");
            return;
        }

        try {
            setLoading(true);

            // Tạo FormData chuẩn
            let form = new FormData();
            for (let key in formData) {
                if (key !== 'confirm') { // Không gửi confirm pass lên server
                    form.append(key, formData[key]);
                }
            }

            // Nếu backend yêu cầu username, gán username = email
            if (!formData.username) {
                form.append("username", formData.email);
            }

            console.info("Sending Employer Data:", formData);

            // Gọi API
            let res = await Apis.post(endpoints['register_employer'], form, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (res.status === 201) {
                Alert.alert("Thành công", "Đăng ký hồ sơ doanh nghiệp thành công! Vui lòng chờ Admin phê duyệt.");
                navigation.navigate('Login');
            }

        } catch (ex) {
            // --- XỬ LÝ LỖI (Mang từ Candidate sang) ---
            let message = "Đăng ký thất bại.";
            if (ex.response && ex.response.data) {
                const errorData = ex.response.data;
                console.log("Lỗi Server:", errorData);

                // Từ điển dịch lỗi cho Employer
                const fieldMap = {
                    "email": "Email",
                    "username": "Tên đăng nhập",
                    "password": "Mật khẩu",
                    "first_name": "Tên người liên hệ",
                    "company_name": "Tên công ty",
                    "phone": "Số điện thoại",
                    "address": "Địa chỉ",
                    "website": "Website",
                    "non_field_errors": "Lỗi chung"
                };

                if (typeof errorData === 'object') {
                    message = "";
                    for (let key in errorData) {
                        let vnField = fieldMap[key] || key;
                        let errContent = errorData[key];
                        if (Array.isArray(errContent)) errContent = errContent[0];

                        let lowerContent = String(errContent).toLowerCase();
                        let vnMessage = "gặp lỗi.";

                        if (lowerContent.includes("already exists")) vnMessage = "đã tồn tại.";
                        else if (lowerContent.includes("required")) vnMessage = "là bắt buộc.";
                        else if (lowerContent.includes("valid")) vnMessage = "không hợp lệ.";

                        message += `• ${vnField} ${vnMessage}\n`;
                    }
                }
            }
            Alert.alert("Thông báo lỗi", message);
        } finally {
            setLoading(false);
        }
    };

    // --- RENDER CÁC BƯỚC (Giữ nguyên UI của bạn) ---

    // STEP 1: Tài khoản cá nhân
    const renderStep1 = () => (
        <View>
            <Text style={styles.sectionTitle}>1. Account Information</Text>

            {/* Thêm trường Tên người liên hệ (Backend User nào cũng cần first_name) */}
            <TextInput
                label="Contact Person Name"
                value={formData.first_name}
                onChangeText={(text) => updateData('first_name', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="account-tie" />}
            />

            <TextInput
                label="Work Email"
                value={formData.email}
                onChangeText={(text) => updateData('email', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="email-outline" />}
                keyboardType="email-address"
                autoCapitalize="none"
            />
            <TextInput
                label="Password"
                value={formData.password}
                onChangeText={(text) => updateData('password', text)}
                secureTextEntry
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="lock-outline" />}
            />
            <TextInput
                label="Confirm Password"
                value={formData.confirm}
                onChangeText={(text) => updateData('confirm', text)}
                secureTextEntry
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="lock-check-outline" />}
            />
        </View>
    );

    // STEP 2: Thông tin công ty
    const renderStep2 = () => (
        <View>
            <Text style={styles.sectionTitle}>2. Company Details</Text>
            <TextInput
                label="Company Name"
                value={formData.companyName} // Lưu ý: key này phải khớp logic backend
                // Ở trên state mình đặt là company_name nhưng logic UI bạn dùng companyName
                // Sửa lại chỗ này cho khớp state:
                onChangeText={(text) => updateData('company_name', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="domain" />}
            />
            <TextInput
                label="Website (Optional)"
                value={formData.website}
                onChangeText={(text) => updateData('website', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="web" />}
                autoCapitalize="none"
            />
        </View>
    );

    // STEP 3: Liên hệ & Xác thực
    const renderStep3 = () => (
        <View>
            <Text style={styles.sectionTitle}>3. Contact & Verify</Text>
            <TextInput
                label="Phone Number"
                value={formData.phone}
                keyboardType="phone-pad"
                onChangeText={(text) => updateData('phone', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="phone" />}
            />
            <TextInput
                label="Headquarters Address"
                value={formData.address}
                onChangeText={(text) => updateData('address', text)}
                mode="outlined"
                style={styles.input}
                left={<TextInput.Icon icon="map-marker" />}
            />
        </View>
    );

    // --- XỬ LÝ ĐIỀU HƯỚNG BƯỚC ---
    const handleNext = () => {
        if (step < 3) {
            setStep(step + 1);
        } else {
            // Ở bước cuối cùng, thay vì log log, ta gọi hàm register
            register();
        }
    };

    const handleBack = () => {
        if (step > 1) setStep(step - 1);
        else navigation.goBack();
    };

    return (
        <View style={styles.container}>
            <ScrollView showsVerticalScrollIndicator={false}>

                {/* Header */}
                <View style={styles.headerContainer}>
                    <Text style={styles.appName}>Job<Text style={styles.brandHighlight}>Link</Text></Text>
                    <Text style={{ color: 'gray' }}>Employer Registration</Text>
                </View>

                {/* Progress Bar (Giữ nguyên) */}
                <View style={styles.progressContainer}>
                    <View style={[styles.stepIndicator, step >= 1 && styles.activeStep]}>
                        <Text style={[styles.stepText, step >= 1 && styles.activeStepText]}>1</Text>
                    </View>
                    <View style={[styles.stepLine, step >= 2 && styles.activeLine]} />

                    <View style={[styles.stepIndicator, step >= 2 && styles.activeStep]}>
                        <Text style={[styles.stepText, step >= 2 && styles.activeStepText]}>2</Text>
                    </View>
                    <View style={[styles.stepLine, step >= 3 && styles.activeLine]} />

                    <View style={[styles.stepIndicator, step >= 3 && styles.activeStep]}>
                        <Text style={[styles.stepText, step >= 3 && styles.activeStepText]}>3</Text>
                    </View>
                </View>

                {/* Nội dung form */}
                {step === 1 && renderStep1()}
                {step === 2 && renderStep2()}
                {step === 3 && renderStep3()}

                {/* Nút điều hướng */}
                <View style={styles.navButtonContainer}>
                    <Button
                        mode="outlined"
                        style={styles.backBtn}
                        textColor="#524B6B"
                        onPress={handleBack}
                        disabled={loading} // Khóa nút khi đang gửi
                    >
                        {step === 1 ? "Cancel" : "Back"}
                    </Button>

                    <Button
                        mode="contained"
                        style={styles.nextBtn}
                        onPress={handleNext}
                        loading={loading} // Hiệu ứng xoay vòng loading
                        disabled={loading}
                    >
                        {step === 3 ? "Submit" : "Next"}
                    </Button>
                </View>

            </ScrollView>
        </View>
    );
};

export default EmployerRegister;