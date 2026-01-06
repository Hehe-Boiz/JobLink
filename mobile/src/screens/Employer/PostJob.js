const handlePost = async () => {

};

import React, { useState, useEffect } from 'react';
import { ScrollView, KeyboardAvoidingView, Platform, Alert, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from 'react-native-paper';

// IMPORT COMPONENTS ĐÃ TÁCH
import AppHeader from '../../components/common/AppHeader';
import AppInput from '../../components/common/AppInput';
import ChipSelector from '../../components/Employer/ChipSelector';
import Apis, { authApis, endpoints } from '../../utils/Apis';
// Style import (Nếu cần style riêng cho container)
import styles from '../../styles/Employer/EmployerStyles';
import AppSelector from '../../components/common/AppSelector';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AppDatePicker from '../../components/common/AppDatePicker';
import { validateForm } from '../../utils/validate/Employer/ValidatePostJob';

const PostJob = ({ navigation }) => {
    // 1. State
    const [jobData, setJobData] = useState({
        title: '', location: '', address: '', salaryMin: '', salaryMax: '',
        description: '', requirements: '', benefits: '', deadline: null
    });
    const [categories, setCategories] = useState([]);
    const [locations, setLocations] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [jobType, setJobType] = useState('FULL_TIME');
    const jobTypes = ['FULL_TIME', 'PART_TIME', 'REMOTE', 'INTERN']
    const [level, setLevel] = useState('JUNIOR');
    const levels = ['INTERN', 'FRESHER', 'JUNIOR', 'MIDDLE', 'SENIOR', 'EXPERT']
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        const fetchData = async () => {
            try {
                let resCat = await Apis.get(endpoints['categories']);
                let resLoc = await Apis.get(endpoints['locations']);
                setCategories(resCat.data);
                setLocations(resLoc.data);
            } catch (e) {
                console.error("Lỗi tải danh mục:", e);
            }
        };
        fetchData();
    }, []);

    const updateData = (key, value) => {
        setJobData(prev => ({ ...prev, [key]: value }));
    };


    const handlePost = async () => {
        const [isValid, errors] = validateForm(jobData);
        if (!isValid) {
            Alert.alert("Vui lòng kiểm tra lại dữ liệu", errors.join("\n"));
            return;
        }
        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);

            let formattedDeadline = null;
            if (jobData.deadline) {
                const d = jobData.deadline;
                formattedDeadline = `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
            }
 
            const payload = {
                title: jobData.title,
                company_name: "Tự động lấy từ Profile", 

                category: selectedCategory.id,
                location: selectedLocation.id,
                address: jobData.address,

                employment_type: jobType,
                experience_level: level,

  
                salary_min: parseInt(jobData.salaryMin) || null,
                salary_max: parseInt(jobData.salaryMax) || null,

                description: jobData.description,
                requirements: jobData.requirements,
                benefits: jobData.benefits,
                deadline: formattedDeadline // YYYY-MM-DD
            };

            console.log("Sending Payload:", payload);

            let res = await api.post(endpoints['employer_jobs'], payload);

            if (res.status === 201) {
                Alert.alert("Thành công", "Đăng tin tuyển dụng thành công!");
                navigation.goBack();
            }

        } catch (ex) {
            console.error(ex);
            let msg = "Lỗi không xác định";
            if (ex.response && ex.response.data) {
                msg = JSON.stringify(ex.response.data); 
            }
            Alert.alert("Đăng tin thất bại", msg);
        } finally {
            setLoading(false);
        }
        console.log("Post:", { ...jobData, jobType });
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: 'white' }} edges={['top', 'left', 'right']}>
            <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>


                <AppHeader
                    title="Đăng Tin Mới"
                    rightIcon="information-outline"
                    onRightPress={() => Alert.alert("Tips", "Điền đủ thông tin để thu hút ứng viên.")}
                />

                <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>

                    <Text style={styles.sectionTitle}>1. Thông tin cơ bản</Text>

                    <AppInput
                        label="Tiêu đề công việc" required
                        placeholder="VD: Senior React Native Dev"
                        value={jobData.title}
                        onChangeText={(t) => updateData('title', t)}
                    />
                    <AppSelector
                        label="Ngành nghề"
                        required
                        placeholder="Chọn ngành nghề..."
                        data={categories}
                        selectedValue={selectedCategory}
                        onSelect={setSelectedCategory}
                    />

                    <AppSelector
                        label="Địa điểm làm việc"
                        required
                        placeholder="Chọn thành phố..."
                        data={locations}
                        selectedValue={selectedLocation}
                        onSelect={setSelectedLocation}
                    />
                    <AppInput
                        label="Địa chỉ công việc" required
                        placeholder="VD: Quận 1, TP.HCM"
                        icon="map-marker-outline"
                        value={jobData.address}
                        onChangeText={(t) => updateData('address', t)}
                    />

                    <ChipSelector
                        label="Trình độ"
                        options={levels}
                        selectedValue={level}
                        onSelect={setLevel}
                    />
                    <ChipSelector
                        label="Hình thức làm việc"
                        options={jobTypes}
                        selectedValue={jobType}
                        onSelect={setJobType}
                    />
                    <AppDatePicker
                        label="Hạn nộp hồ sơ"
                        placeholder="Chọn ngày hết hạn..."
                        value={jobData.deadline}
                        onDateChange={(date) => updateData('deadline', date)}
                    />
                    {/* PHẦN 2: LƯƠNG */}
                    <Text style={styles.sectionTitle}>2. Mức lương (Triệu VNĐ)</Text>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                        <AppInput
                            label="Từ" keyboardType="numeric" style={{ width: '48%' }}
                            value={jobData.salaryMin} onChangeText={(t) => updateData('salaryMin', t)}
                        />
                        <AppInput
                            label="Đến" keyboardType="numeric" style={{ width: '48%' }}
                            value={jobData.salaryMax} onChangeText={(t) => updateData('salaryMax', t)}
                        />
                    </View>


                    <Text style={styles.sectionTitle}>3. Chi tiết & Yêu cầu</Text>

                    <AppInput
                        label="Mô tả công việc" required multiline numberOfLines={4}
                        value={jobData.description} onChangeText={(t) => updateData('description', t)}
                    />

                    <AppInput
                        label="Yêu cầu ứng viên" multiline numberOfLines={4}
                        value={jobData.requirements} onChangeText={(t) => updateData('requirements', t)}
                    />

                    <AppInput
                        label="Quyền lợi" multiline numberOfLines={3}
                        value={jobData.benefits} onChangeText={(t) => updateData('benefits', t)}
                    />


                    <Button
                        mode="contained"
                        onPress={handlePost}
                        loading={loading}
                        disabled={loading}
                        style={styles.btnPrimary} 
                        contentStyle={{ height: 50 }}
                    >
                        ĐĂNG TUYỂN DỤNG
                    </Button>

                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

export default PostJob;