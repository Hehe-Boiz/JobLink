import React, { useState, useEffect, useCallback } from 'react';
import { View, TouchableOpacity, FlatList, ActivityIndicator, TextInput, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Imports
import CustomText from '../../components/common/CustomText';
import CustomHeader from '../../components/common/CustomHeader';
import { authApis, endpoints } from '../../utils/Apis';
import ApplicantItem from '../../components/Employer/ApplicantItem';
import styles, { COLORS } from '../../styles/Employer/JobApplicantsStyles';

const JobApplicants = ({ route, navigation }) => {
    const { job } = route.params || {};

    const [applicants, setApplicants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    
    // --- State Search & Pagination ---
    const [searchText, setSearchText] = useState('');
    const [q, setQ] = useState(""); 
    const [page, setPage] = useState(1);
    
    // --- Debounce Search ---
    useEffect(() => {
        const timer = setTimeout(() => {
            setQ(searchText);
        }, 500);
        return () => clearTimeout(timer);
    }, [searchText]);

    // --- Reset Page khi Search ---
    useEffect(() => {
        if (q !== "") {
            setLoading(true);
            setPage(1);
        }
    }, [q]);

    // --- Hàm tải dữ liệu ---
    const loadApplicants = async () => {
        if (!job?.id) return;
        if (page === 0) return;

        try {
            if (page === 1 && !refreshing) setLoading(true);

            const token = await AsyncStorage.getItem('token');
            let url = `${endpoints['applications_by_employer_jobs'](job.id)}&page=${page}`;
            if (q) url += `&q=${q}`;

            const res = await authApis(token).get(url);

            if (res.data.next === null) setPage(0);

            if (page === 1) {
                setApplicants(res.data.results);
            } else {
                setApplicants(prev => [...prev, ...res.data.results]);
            }
        } catch (ex) {
            console.error("Lỗi tải danh sách ứng viên:", ex);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    // --- Trigger tải dữ liệu ---
    useEffect(() => {
        if (page > 0) loadApplicants();
    }, [page, job]);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        setPage(1);
    }, []);

    const loadMore = () => {
        if (page > 0 && !loading && applicants.length > 0) {
            setPage(page + 1);
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader 
                title="Danh sách ứng viên" 
                navigation={navigation} 
                isBack={true} 
                style={{backgroundColor: COLORS.background}} 
            />

            {/* Header thông tin Job */}
            <View style={styles.jobHeader}>
                <View style={styles.jobIconBox}>
                    <MaterialCommunityIcons name="briefcase-variant-outline" size={26} color={COLORS.primary} />
                </View>
                <View style={{ flex: 1 }}>
                    <CustomText style={styles.jobTitle} numberOfLines={1}>{job?.title}</CustomText>
                    <CustomText style={styles.jobSub}>
                        Đang hiển thị: <CustomText style={{ fontWeight: 'bold', color: COLORS.primary }}>{applicants.length}</CustomText> hồ sơ
                    </CustomText>
                </View>
            </View>

            {/* Search Box */}
            <View style={styles.searchContainer}>
                <View style={styles.searchBoxModern}>
                    <MaterialCommunityIcons name="magnify" size={26} color={COLORS.placeholder} style={{marginLeft: 5}} />
                    <TextInput
                        placeholder="Tìm tên hoặc email..."
                        style={styles.searchInputModern}
                        value={searchText}
                        onChangeText={setSearchText}
                        placeholderTextColor={COLORS.placeholder}
                        autoCapitalize="none"
                        backgroundColor="transparent" 
                    />
                    {searchText.length > 0 && (
                        <TouchableOpacity onPress={() => setSearchText('')} hitSlop={{top: 15, bottom: 15, left: 15, right: 15}}>
                            <MaterialCommunityIcons name="close-circle" size={22} color={COLORS.placeholder} />
                        </TouchableOpacity>
                    )}
                </View>
            </View>

            {/* Danh sách ứng viên */}
            {loading && page === 1 ? (
                <View style={styles.centerBox}>
                    <ActivityIndicator size="large" color={COLORS.primary} />
                    <CustomText style={{ marginTop: 10, color: COLORS.secondary }}>
                        Đang tải danh sách...
                    </CustomText>
                </View>
            ) : (
                <FlatList
                    data={applicants}
                    keyExtractor={(item) => item.id.toString()}
                    
                    // Render Item dùng Component mới tách ra
                    renderItem={({ item }) => (
                        <ApplicantItem 
                            item={item} 
                            onPress={() => navigation.navigate('CandidateDetail', { application: item })} 
                        />
                    )}
                    
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} tintColor={COLORS.primary} />
                    }
                    onEndReached={loadMore}
                    onEndReachedThreshold={0.5}
                    ListFooterComponent={
                        (loading && page > 1) ? (
                            <View style={{ padding: 10, alignItems: 'center' }}>
                                <ActivityIndicator size="small" color={COLORS.primary} />
                            </View>
                        ) : null
                    }
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <MaterialCommunityIcons name="account-search-outline" size={80} color="#DDD" style={{marginBottom: 15}} />
                            <CustomText style={{ color: '#999', fontSize: 16, textAlign: 'center' }}>
                                {q ? `Không tìm thấy ứng viên nào cho\n"${q}"` : "Chưa có ứng viên nào ứng tuyển."}
                            </CustomText>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
};

export default JobApplicants;