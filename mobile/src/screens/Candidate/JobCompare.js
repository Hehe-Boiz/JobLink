import React, {useEffect, useState} from "react";
import {
    View,
    ScrollView,
    Image,
    TouchableOpacity,
    StatusBar,
    ActivityIndicator,
    Alert,
    useWindowDimensions
} from "react-native";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomText from "../../components/common/CustomText";
import CustomHeader from "../../components/common/CustomHeader";
import {SafeAreaView} from "react-native-safe-area-context";
import styles from "../../styles/Candidate/JobCompareStyles";
import Apis, {authApis, endpoints} from "../../utils/Apis";
import AsyncStorage from "@react-native-async-storage/async-storage";
import RenderHTML from "react-native-render-html"

const JOB_COLORS = [
    "#130160",
    "#F28B2C",
    "#2E7D32",
    "#C2185B",
    "#0288D1",
];

const JobValueRow = ({value, color, companyName, isLast}) => {
    const {width} = useWindowDimensions();
    const isHTML = typeof value === 'string' && /<[a-z][\s\S]*>/i.test(value);

    return (
        <View style={[styles.jobRow, {borderLeftColor: color}, isLast && styles.jobRowLast]}>
            <View style={styles.jobRowContent}>
                {isHTML ? (
                    <RenderHTML
                        contentWidth={width}
                        source={{html: value}}
                        baseStyle={{fontSize: 14, color: '#333'}}
                    />
                ) : (
                    <CustomText style={styles.jobValue}>
                        {value || "---"}
                    </CustomText>
                )}
                <CustomText style={styles.companyNameSmall}>{companyName}</CustomText>
            </View>
        </View>
    );
};

const ComparisonSection = ({title, jobs, dataKey, colors, formatFn}) => {
    return (
        <View style={styles.cardContainer}>
            <CustomText style={styles.cardTitle}>{title}</CustomText>

            {jobs.map((job, index) => {
                const displayValue = formatFn(job, dataKey);
                const color = colors[index % colors.length];

                return (
                    <JobValueRow
                        key={job.id}
                        value={displayValue}
                        color={color}
                        companyName={job.company_name}
                        isLast={index === jobs.length - 1}
                    />
                );
            })}
        </View>
    );
};

const JobComparison = ({navigation, route}) => {
    const selectedJobs = route.params.selectedJobs;
    const [sameCategory, setSameCategory] = useState(true);
    const [detailedJobs, setDetailedJobs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (selectedJobs.length > 0) {
            fetchComparisonData();
        }
    }, []);

    const fetchComparisonData = async () => {
        try {
            setLoading(true);
            const ids = selectedJobs.map(j => j.id).join(',');
            const token = await AsyncStorage.getItem('token')
            const res = await authApis(token).get(`${endpoints['compare']}?ids=${ids}`);
            console.log(res.data)

            setDetailedJobs(res.data.data);
            setSameCategory(res.data.same_category);

        } catch (error) {
            console.error("Lỗi so sánh:", error);
            Alert.alert("Lỗi", "Không thể tải dữ liệu so sánh lúc này.");
        } finally {
            setLoading(false);

        }
    };

    const formatValue = (job, key) => {
        const val = job[key];
        if (!val) return "---";
        if (Array.isArray(val)) return val.map(t => t.name || t).join(", ");
        if (typeof val === 'object') return val.name || "---";
        if (['benefits', 'requirements', 'description'].includes(key)) {
            return val;
        }

        if (key === 'employment_type' || key === 'experience_level') {
            return val.charAt(0) + val.slice(1).toLowerCase().replace('_', ' ');
        }

        return val;
    };

    if (loading) {
        return (
            <SafeAreaView style={[styles.container, {justifyContent: 'center'}]}>
                <ActivityIndicator size="large" color="#130160"/>
                <CustomText style={{alignSelf: 'center', marginTop: 10}}>Đang phân tích dữ liệu...</CustomText>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="dark-content" backgroundColor="#F2F3F7"/>
            <CustomHeader navigation={navigation} title="So sánh chi tiết"/>

            <View style={styles.headerContainer}>
                <CustomText style={styles.headerTitle}>So sánh {selectedJobs.length} công việc</CustomText>
                <CustomText style={styles.subHeader}>Kéo ngang để xem danh sách công ty</CustomText>
            </View>

            <View>
                <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    style={styles.legendScroll}
                    contentContainerStyle={styles.legendContent}
                >
                    {detailedJobs.map((job, index) => {
                        const color = JOB_COLORS[index % JOB_COLORS.length];
                        return (
                            <View key={job.id} style={[styles.legendItem, {borderColor: color}]}>
                                <Image source={{uri: job.employer_logo}} style={styles.legendLogo}/>
                                <CustomText numberOfLines={1} style={styles.legendText}>
                                    {job.company_name}
                                </CustomText>
                            </View>
                        );
                    })}
                </ScrollView>
            </View>

            <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>

                <ComparisonSection
                    title="Mức lương"
                    jobs={detailedJobs}
                    dataKey="salary_max"
                    colors={JOB_COLORS}
                    formatFn={formatValue}

                />

                <ComparisonSection
                    title="Yêu cầu kỹ năng"
                    jobs={detailedJobs}
                    dataKey="tags"
                    colors={JOB_COLORS}
                    formatFn={formatValue}
                />

                <ComparisonSection
                    title="Kinh nghiệm yêu cầu"
                    jobs={detailedJobs}
                    dataKey="experience_level"
                    colors={JOB_COLORS}
                    formatFn={formatValue}
                />

                <ComparisonSection
                    title="Hình thức làm việc"
                    jobs={detailedJobs}
                    dataKey="employment_type"
                    colors={JOB_COLORS}
                    formatFn={formatValue}
                />

                <ComparisonSection
                    title="Phúc lợi"
                    jobs={detailedJobs}
                    dataKey="benefits"
                    colors={JOB_COLORS}
                    formatFn={formatValue}
                />


            </ScrollView>

            <View style={styles.footerActions}>
                <TouchableOpacity
                    style={[styles.applyBtn, {backgroundColor: '#130160'}]}
                    onPress={() => {
                        navigation.goBack();
                    }}
                >
                    <MaterialCommunityIcons name="arrow-left" size={20} color="#FFF"/>
                    <CustomText style={styles.applyText}>Quay lại danh sách</CustomText>
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
};

export default JobComparison;