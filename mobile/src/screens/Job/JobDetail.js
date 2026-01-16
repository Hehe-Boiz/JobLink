import React, { useState, useMemo, useContext, useEffect } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { ScrollView, TouchableOpacity, View, StyleSheet, Image, Alert, ActivityIndicator } from "react-native";
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from "../../components/common/CustomText";
import JobDescriptionTab from "../../components/Job/JobDetail/JobDetailDescription";
import CompanyTab from "../../components/Job/JobDetail/JobDetailCompany";
import styles from '../../styles/Job/JobDetailStyles'
import JobApplicantsTab from "../../components/Job/JobDetail/JobApplicantsTab";
import { MyUserContext } from "../../utils/contexts/MyContext";
import { Portal, Dialog, Button } from 'react-native-paper';
import JobLogo from "../../components/Job/JobLogo";
import CustomHeader from "../../components/common/CustomHeader"
import CustomFooter from "../../components/common/CustomFooter";
import Apis, { endpoints, authApis } from '../../utils/Apis';
import { formatTimeElapsed, stripHtmlTags } from "../../utils/Helper";
import AsyncStorage from "@react-native-async-storage/async-storage";

const MOCK_APPLICANTS = [
    {
        id: 1,
        name: 'Nguyễn Văn An',
        email: 'an.nguyen@email.com',
        status: 'Chờ duyệt',
        statusColor: '#FF9228',
        bg: '#FFF4E5',
        avatar: 'https://randomuser.me/api/portraits/men/32.jpg'
    },
    {
        id: 2,
        name: 'Phạm Thị Dung',
        email: 'dung.pham@email.com',
        status: 'Đã xem',
        statusColor: '#2E5CFF',
        bg: '#E6E1FF',
        avatar: 'https://randomuser.me/api/portraits/women/44.jpg'
    },
    {
        id: 3,
        name: 'Lê Hoàng',
        email: 'hoang.le@email.com',
        status: 'Từ chối',
        statusColor: '#FF4D4D',
        bg: '#FFECEC',
        avatar: 'https://randomuser.me/api/portraits/men/45.jpg'
    },
];


const JobDetail = ({ navigation, route }) => {
    const { jobId, initialData } = route.params || {};
    const [user,] = useContext(MyUserContext)
    const applicants = MOCK_APPLICANTS;
    const [activeTab, setActiveTab] = useState(0);
    const [isSaved, setIsSaved] = useState(false);
    const isEmployer = user?.role === "EMPLOYER";
    const toggleSave = async () => {
        const prevSaved = isSaved;
        setIsSaved(!isSaved);

        try {
            const api = authApis(user.token);
            if (prevSaved) {
                if (job.bookmark_id) {
                    await api.delete(`${endpoints['bookmarks']}${job.bookmark_id}/`);
                    setJob(prev => ({ ...prev, bookmark_id: null }));
                }
            } else {
                const res = await api.post(endpoints['bookmarks'], { job_id: job.id });
                setJob(prev => ({ ...prev, bookmark_id: res.data.id }));
            }
        } catch (error) {
            console.error(error);
            setIsSaved(prevSaved);
            Alert.alert("Lỗi", "Không thể cập nhật trạng thái lưu.");
        }
    };

    const mapJobData = (data) => {
        if (!data) return null;

        const minSalary = data.salary_min ? (data.salary_min / 1000000).toFixed(0) + 'M' : '';
        const maxSalary = data.salary_max ? (data.salary_max / 1000000).toFixed(0) + 'M' : '';
        const salaryString = (minSalary && maxSalary)
            ? `${minSalary} - ${maxSalary}`
            : (minSalary || maxSalary || 'Thỏa thuận');

        return {
            id: data.id,
            logo: data.employer_logo || data.logo || 'https://via.placeholder.com/150',
            title: data.title,
            company: data.company_name || data.company || "Unknown Company",
            location: data.location?.name || data.location || "Việt Nam",
            postedTime: formatTimeElapsed(data.updated_date || new Date()), // Format thời gian

            desc: stripHtmlTags(data.description) || "Đang tải chi tiết...",
            requirements: stripHtmlTags(data.requirements) || "Đang tải yêu cầu...",
            street: stripHtmlTags(data.company?.address) || "Chưa cập nhật địa chỉ",

            info: [
                { title: "Mức lương", value: salaryString },
                { title: "Kinh nghiệm", value: data.experience ? `${data.experience} năm` : "Không yêu cầu" },
                { title: "Hình thức", value: data.employment_type?.replace('_', ' ') || "Full Time" },
                { title: "Hạn nộp", value: data.deadline ? new Date(data.deadline).toLocaleDateString() : "Vô thời hạn" },
            ],

            facilities: stripHtmlTags(data.benefits) || "Chưa có thông tin đãi ngộ",

            companyData: {
                about: stripHtmlTags(data.company?.description) || "Đang tải thông tin...",
                website: data.company?.website || null, // Lấy link website
                address: data.company?.address || "Việt Nam",
                gallery: [
                    "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800",
                    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800"
                ],
                info: [
                    {
                        title: "Quy mô",
                        value: data.company?.company_size ? `${data.company.company_size} nhân viên` : "N/A"
                    },
                    { title: "Quốc gia", value: data.company?.country?.name || "Việt Nam" },
                    { title: "Thành lập", value: data.company?.founded_year || "N/A" },
                ]
            },

            bookmark_id: data.bookmark_id
        };
    };

    const [job, setJob] = useState(() => initialData ? mapJobData(initialData) : null);
    const [loading, setLoading] = useState(!job);

    useEffect(() => {
        const loadFullDetail = async () => {
            if (!jobId) return;
            try {
                const token = await AsyncStorage.getItem('token')
                const res = await authApis(token).get(`${endpoints['jobs']}${jobId}/`);

                const fullData = mapJobData(res.data);
                setJob(fullData);

                setIsSaved(!!res.data.bookmark_id);

            } catch (error) {
                console.error("Lỗi tải chi tiết job:", error);
            } finally {
                setLoading(false);
            }
        };

        loadFullDetail();
    }, [jobId, user?.token]);

    const SaveButton = (
        <TouchableOpacity style={styles.btnBookmark} onPress={toggleSave}>
            <MaterialCommunityIcons
                name={isSaved ? "bookmark" : "bookmark-outline"}
                size={28}
                color={isSaved ? "#FF9228" : "#FCA34D"}
            />
        </TouchableOpacity>
    );

    const handleApply = () => {
        navigation.navigate('ApplyJob', { jobId: job.id, jobTitle: job.title });
    };

    if (loading && !job) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color="#FF9228" />
            </View>
        );
    }

    if (!job) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <CustomText>Không tìm thấy công việc.</CustomText>
            </View>
        );
    }

    // const isEmployer = user.role == "EMPLOYER" ? true : false;
    return (
        <View style={{ flex: 1 }}>
            <SafeAreaView style={[styles.container]} edges={['top', 'left', 'right']}>
                <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 130 }}>
                    <CustomHeader navigation={navigation} />

                    <View style={styles.section}>
                        <JobLogo item={job} />
                        {isEmployer && (
                            <TouchableOpacity
                                style={styles.viewCandidateButton}
                                onPress={() => navigation.navigate('JobApplicants', { job: job })}
                            >
                                <MaterialCommunityIcons name="account-group" size={20} color="#1976D2" style={{ marginRight: 8 }} />
                                <CustomText style={styles.viewCandidateButtonText}>
                                    Xem danh sách ứng viên
                                </CustomText>
                            </TouchableOpacity>
                        )}
                        <View style={styles.tabContainer}>
                            <TouchableOpacity
                                style={[styles.tabButton, activeTab === 0 && styles.activeTab]}
                                onPress={() => setActiveTab(0)}
                            >
                                <CustomText style={[styles.tabText, activeTab === 0 && styles.activeTabText]}>
                                    Description
                                </CustomText>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={[styles.tabButton, activeTab === 1 && styles.activeTab]}
                                onPress={() => setActiveTab(1)}
                            >
                                <CustomText style={[styles.tabText, activeTab === 1 && styles.activeTabText]}>
                                    Company
                                </CustomText>
                            </TouchableOpacity>
                        </View>
                        {activeTab === 0 && <JobDescriptionTab item={job} />}
                        {activeTab === 1 && <CompanyTab item={job.companyData} />}
                    </View>
                </ScrollView>
            </SafeAreaView>
            {!isEmployer && (
                <CustomFooter
                    onApply={handleApply}
                    leftContent={SaveButton}
                />
            )}
        </View>
    );
};

export default JobDetail;


