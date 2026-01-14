import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, TextInput, RefreshControl } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from "@react-native-async-storage/async-storage";
import styles from '../../styles/Employer/EmployerStyles';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import JobCard from '../../components/Employer/JobCard';
import { useDialog } from '../../hooks/useDialog';
import { useIsFocused } from '@react-navigation/native';
import { useEmployer } from '../../hooks/useEmployer';
const EmployerJobs = ({ navigation }) => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchText, setSearchText] = useState('');
    const [q, setQ] = useState("");
    const [page, setPage] = useState(1);
    const { showDialog } = useDialog();
    const isFocused = useIsFocused();
    const { profile } = useEmployer();

    const loadJobs = async () => {
        if (profile && profile.is_verified === false) {
            console.log('oke')
            setLoading(false);
            showDialog({
                type: 'error',
                title: 'Chưa được duyệt',
                content: 'Tài khoản Nhà tuyển dụng của bạn chưa được Admin phê duyệt. Vui lòng liên hệ quản trị viên để được kích hoạt.',
                confirmText: 'ĐÃ HIỂU'
            });
            setJobs([]);
            return;
        }
        try {
            setLoading(true);
            let url = `${endpoints['employer_jobs']}?page=${page}`;
            if (q) {
                url = `${url}&q=${q}`;
            }
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);

            let res = await api.get(url);
            if (res.data.next === null)
                setPage(0);
            if (page === 1)
                setJobs(res.data.results);
            else if (page > 1)
                setJobs([...jobs, ...res.data.results]);
        } catch (ex) {
            console.error(ex);
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => {
        if (isFocused) {
            setPage(1);
        }
    }, [isFocused]);
    useEffect(() => {
        console.log(profile);
        let timer = setTimeout(() => {
            if (page > 0)
                loadJobs();
        }, 500);

        return () => clearTimeout(timer);
    }, [page, profile]);

    useEffect(() => {
        setPage(1);
    }, [q]);
    const loadMore = () => {
        if (page > 0 && !loading && jobs.length > 0)
            setPage(page + 1);
    }
    const deleteJob = async (jobId) => {
        try {
            const token = await AsyncStorage.getItem('token');
            let res = await authApis(token).delete(endpoints['delete_jobs'](jobId));
            setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
            if (res.status === 200) {
                showDialog({
                    type: 'success',
                    title: 'Thành công',
                    content: 'Đã xóa tin tuyển dụng.'
                });
            }
        } catch (ex) {
            console.error(ex);
            showDialog({
                type: 'error',
                title: 'Lỗi',
                content: 'Không thể xóa tin lúc này.'
            });
        }
    }
    const handleDeleteJob = (jobId) => {
        showDialog({
            type: 'warning',
            title: 'Xác nhận xóa',
            content: 'Tin tuyển dụng này sẽ bị ẩn khỏi hệ thống. Bạn có chắc chắn không?',
            confirmText: 'ĐỒNG Ý',
            cancelText: 'HỦY',
            showCancel: true,
            onConfirm: () => deleteJob(jobId)
        });
    };
    const handleEditJob = (job) => {
        navigation.navigate('PostJob', { jobData: job, isEdit: true });
    };

    const filteredJobs = jobs.filter(job =>
        job.title.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9F9F9' }} edges={['top']}>

            <View style={{ padding: 20, backgroundColor: 'white', paddingBottom: 10 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                    <View>
                        <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#130160' }}>Quản lý tin</Text>
                        <Text style={{ color: '#95969D' }}>Bạn đang có {jobs.length} tin tuyển dụng</Text>
                    </View>

                    <TouchableOpacity
                        onPress={() => navigation.navigate('PostJob')}
                        style={{ backgroundColor: '#130160', width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' }}
                    >
                        <MaterialCommunityIcons name="plus" size={24} color="white" />
                    </TouchableOpacity>
                </View>

                <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#F5F7FA', borderRadius: 12, paddingHorizontal: 15, height: 50 }}>
                    <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9" />
                    <TextInput
                        placeholder="Tìm kiếm tin tuyển dụng..."
                        style={{ flex: 1, marginLeft: 10, fontSize: 15 }}
                        value={searchText}
                        onChangeText={setSearchText}
                    />
                </View>
            </View>

            {loading && page === 1 ? (
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                    <ActivityIndicator size="large" color="#130160" />
                    <Text style={{ marginTop: 10, color: '#524B6B' }}>Đang tải dữ liệu...</Text>
                </View>
            ) : (
                <FlatList
                    data={filteredJobs}
                    keyExtractor={item => item.id.toString()}
                    contentContainerStyle={{ padding: 20, paddingBottom: 80 }}
                    refreshControl={
                        <RefreshControl
                            refreshing={loading && page === 1}
                            onRefresh={() => setPage(1)} 
                        />
                    }
                    renderItem={({ item }) => (
                        <JobCard
                            job={item}
                            onPress={() => navigation.navigate('JobDetail', { job: item })}
                            onEdit={() => handleEditJob(item)}
                            onDelete={() => handleDeleteJob(item.id)}
                        />
                    )}
                    ListEmptyComponent={
                        <View style={{ alignItems: 'center', marginTop: 50 }}>
                            <MaterialCommunityIcons name="clipboard-text-off-outline" size={60} color="#DDD" />
                            <Text style={{ marginTop: 10, color: '#999' }}>Không tìm thấy tin nào.</Text>
                        </View>
                    }
                    ListFooterComponent={
                        (loading && page > 1) ? (
                            <View style={{ padding: 10 }}>
                                <ActivityIndicator size="small" color="#130160" />
                            </View>
                        ) : null
                    }
                    onEndReached={loadMore}
                    onEndReachedThreshold={0.5}
                />
            )}
        </SafeAreaView>
    );
};

export default EmployerJobs;