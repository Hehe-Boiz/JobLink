import React, {useState, useEffect} from 'react';
import {View, TouchableOpacity, Image, ScrollView, TextInput, Alert, ActivityIndicator} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/Job/ApplyJobStyles';
import CustomHeader from "../../components/common/CustomHeader";
import stylesJobDetail from "../../styles/Job/JobDetailStyles";
import JobLogo from "../../components/Job/JobLogo";
import CustomFooter from "../../components/common/CustomFooter";
import Apis, {endpoints, authApis} from '../../utils/Apis';
import AsyncStorage from "@react-native-async-storage/async-storage";


// const SUCCESS_IMG = 'https://cdn-icons-png.flaticon.com/512/7518/7518748.png';
const SUCCESS_IMG = require('../../../assets/images/Illustration.png')

const job = {
    title: 'UI/UX Designer',
    company: 'Google',
    location: 'California',
    postedTime: '1 day ago',
    logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png'
};

const ApplyJob = ({navigation, route}) => {
    const {jobId} = route.params || {};
    console.log("Job ID nhận được:", jobId);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [jobData, setJobData] = useState(null);
    const [loading, setLoading] = useState(true);

    const [cvFile, setCvFile] = useState(null);
    const [coverLetter, setCoverLetter] = useState('');
    const [isSuccess, setIsSuccess] = useState(false);
    const pickDocument = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: ['application/pdf', 'application/msword'],
                copyToCacheDirectory: true,
            });
            if (result.canceled === false && result.assets && result.assets.length > 0) {
                // Expo Document Picker trả về mảng assets
                setCvFile(result.assets[0]);
            }
        } catch (err) {
            console.log("Lỗi chọn file:", err);
        }
    }

    useEffect(() => {
        const loadJobDetail = async () => {
            if (!jobId) return;
            try {
                const token = await AsyncStorage.getItem('token')
                const api = authApis(token);
                const [jobRes, historyRes] = await Promise.all([
                    api.get(`${endpoints['jobs']}${jobId}/`),

                    api.get(endpoints['candidate_applications'])
                ]);
                setJobData(jobRes.data);
                const hasApplied = historyRes.data.some(app => app.job.id === parseInt(jobId));
                if (hasApplied) {
                    console.log(`[Check] Job ${jobId} đã tồn tại trong danh sách ứng tuyển -> Success`);
                    setIsSuccess(true); // Chuyển thẳng sang màn hình thành công
                } else {
                    console.log(`[Check] Job ${jobId} chưa ứng tuyển -> Hiển thị Form`);
                }
            } catch (error) {
                console.error("Lỗi lấy chi tiết job:", error);
                Alert.alert("Lỗi", "Không thể tải thông tin công việc.");
                navigation.goBack();
            } finally {
                setLoading(false);
            }
        };

        loadJobDetail();
    }, [jobId]);

    const handleApply = async () => {
        if (!cvFile) {
            console.log("2. [Check] Chưa có CV -> Hiển thị Alert");
            Alert.alert("Thiếu thông tin", "Vui lòng tải lên CV của bạn!");
            return;
        }
        setIsSuccess(true);
        try {
            const formData = new FormData();
            formData.append('job', jobId);
            formData.append('cover_letter', coverLetter);
            formData.append('cv', {
                uri: cvFile.uri,
                name: cvFile.name || 'cv.pdf',
                type: cvFile.mimeType || 'application/pdf'
            });

            console.log("Đang gửi đơn ứng tuyển...", formData);

            const token = await AsyncStorage.getItem('token');
            let res = await authApis(token).post(endpoints['candidate_applications'], formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            console.log("Ứng tuyển thành công:", res.data);
            setIsSuccess(true);
        } catch (error) {
            console.error("Lỗi ứng tuyển:", error);
            if (error.response && error.response.data) {
                const msg = error.response.data.detail || JSON.stringify(error.response.data);
                Alert.alert("Không thành công", msg);
            } else {
                Alert.alert("Lỗi", "Có lỗi xảy ra khi nộp đơn. Vui lòng thử lại.");
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <SafeAreaView style={[styles.container, {justifyContent: 'center', alignItems: 'center'}]}>
                <ActivityIndicator size="large" color="#FF9228"/>
            </SafeAreaView>
        );
    }
    if (!jobData) return null;

    const formattedJob = {
        title: jobData.title,
        company: jobData.company_name,
        location: jobData.location?.name || "Vietnam",
        postedTime: jobData.created_date ? `Posted ${jobData.created_date}` : "Recently",
        logo: jobData.employer_logo || 'https://via.placeholder.com/150',
        website: jobData.website
    };

    if (isSubmitting) {
        return (
            <SafeAreaView style={[styles.container, {justifyContent: 'center', alignItems: 'center'}]}>
                <ActivityIndicator size="large" color="#FF9228"/>
                <CustomText style={{marginTop: 10}}>Sending Application...</CustomText>
            </SafeAreaView>
        )
    }


    if (isSuccess) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={{position: 'absolute', top: 50, left: 20}}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#0D0140"/>
                    </TouchableOpacity>
                </View>

                <View style={styles.successContainer}>
                    {/*<Image source={{uri: SUCCESS_IMG}} style={styles.successImage} resizeMode="contain"/>*/}
                    <Image source={SUCCESS_IMG} style={styles.successImage} resizeMode="contain"/>


                    <CustomText style={styles.successTitle}>Successful</CustomText>
                    <CustomText style={styles.successDesc}>
                        Congratulations, your application has been sent
                    </CustomText>

                    <TouchableOpacity style={styles.secondaryBtn} onPress={() => navigation.goBack()}>
                        <CustomText style={styles.secondaryBtnText}>FIND A SIMILAR JOB</CustomText>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.primaryBtn}
                        onPress={() => navigation.navigate('CandidateMain')}
                    >
                        <CustomText style={styles.applyBtnText}>BACK TO HOME</CustomText>
                    </TouchableOpacity>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <CustomHeader title="Apply Job" onBack={() => navigation.goBack()} navigation={navigation}/>
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingBottom: 130}}>

                <View style={stylesJobDetail.section}>
                    <JobLogo item={formattedJob}/>
                    <View style={[stylesJobDetail.containerJob, stylesJobDetail.mt_10]}>
                        <CustomText style={stylesJobDetail.contentTitle}>Upload CV</CustomText>
                        <CustomText style={[stylesJobDetail.contentReq, stylesJobDetail.mb_20]}>Add your CV/Resume to
                            apply
                            for a job</CustomText>
                        {!cvFile ? (
                            <TouchableOpacity style={styles.uploadBox} onPress={pickDocument}>
                                <MaterialCommunityIcons name="cloud-upload-outline" size={24} color="#524B6B"/>
                                <CustomText style={styles.uploadText}>Upload CV/Resume</CustomText>
                            </TouchableOpacity>
                        ) : (
                            <View style={styles.fileSuccessContainer}>
                                <View style={styles.filePreviewContainer}>
                                    <View style={styles.fileIconBox}>
                                        <MaterialCommunityIcons name="file-pdf-box" size={40} color="#FF4D4D"/>
                                    </View>
                                    <View style={styles.fileInfo}>
                                        <CustomText style={styles.fileName} numberOfLines={1}>
                                            {cvFile.name}
                                        </CustomText>
                                        <CustomText style={styles.fileSize}>
                                            {(cvFile.size / 1024).toFixed(0)} Kb • {new Date().toLocaleDateString()}
                                        </CustomText>
                                    </View>
                                    <TouchableOpacity style={styles.removeBtn} onPress={() => setCvFile(pickDocument)}>
                                        <MaterialCommunityIcons name="pencil-outline" size={20} color="#130160"/>
                                    </TouchableOpacity>
                                </View>
                                <TouchableOpacity
                                    style={{flexDirection: 'row', alignItems: 'center', marginTop: 10}}
                                    onPress={() => setCvFile(null)}
                                >
                                    <MaterialCommunityIcons name="trash-can-outline" size={20} color="#FF4D4D"/>
                                    <CustomText style={styles.removeText}>Remove file</CustomText>
                                </TouchableOpacity>
                            </View>
                        )}
                        <CustomText
                            style={[stylesJobDetail.contentTitle, stylesJobDetail.mt_20]}>Information</CustomText>
                        <TextInput
                            style={styles.inputArea}
                            placeholder="Explain why you are the right person for this job..."
                            placeholderTextColor="#AAA6B9"
                            multiline={true}
                            value={coverLetter}
                            onChangeText={setCoverLetter}
                        />
                    </View>
                </View>
            </ScrollView>
            <CustomFooter
                onApply={handleApply}
            />
        </SafeAreaView>
    );
};

export default ApplyJob;