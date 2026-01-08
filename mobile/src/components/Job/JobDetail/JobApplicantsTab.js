import React, { useState, useEffect } from 'react';
import { View, FlatList, TouchableOpacity, Image, StyleSheet, TouchableNativeFeedbackComponent } from 'react-native';
import CustomText from '../../common/CustomText';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { authApis, endpoints } from '../../../utils/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';



const JobApplicantsTab = ({ job }) => {
    const [applicants, setApplicants] = useState([]);
    const [loading, setLoading] = useState(true);
    const load_applicants = async () => {
        try{
            const token = await AsyncStorage.getItem('token');
            setLoading(true);
            let res = await authApis(token).get(endpoints['applications_by_employer_jobs'](job.id));
            setApplicants(res.data);
            setLoading(false);
        }catch(ex){
            console.error(ex);
        }finally{
            setLoading(false);
        }
    }
    const navigation = useNavigation();

    useEffect(() => {
        load_applicants();
    }, []);

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={styles.card}
            onPress={() => navigation.navigate('CandidateDetail', { application: item })}
        >
            <Image source={{ uri: item.candidate_avatar || 'https://randomuser.me/api/portraits/men/32.jpg'}} style={styles.avatar} />
            <View style={styles.content}>
                <View style={styles.rowBetween}>
                    <CustomText style={styles.name}>{item.candidate_name}</CustomText>
                    <View style={[styles.badge]}>
                        <CustomText style={[styles.badgeText, { color: 'red' }]}>
                            {item.status}
                        </CustomText>
                    </View>
                </View>
                <CustomText style={styles.email}>{item.candidate_email}</CustomText>
                <CustomText style={styles.date}>Đã nộp: 20/05/2025</CustomText>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#AAA6B9" />
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <CustomText style={styles.title}>Danh sách ứng viên ({applicants.length})</CustomText>
            </View>
            {applicants.map((item) => (
                <View key={item.id}>
                    {renderItem({ item })}
                </View>
            ))}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        paddingTop: 20,
        paddingHorizontal: 20,
        backgroundColor: 'white',
        minHeight: 300,
    },
    header: {
        marginBottom: 15,
    },
    title: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#130160',
    },
    card: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 15,
        borderBottomWidth: 1,
        borderBottomColor: '#F0F0F0',
        backgroundColor: '#fff',
    },
    avatar: {
        width: 50,
        height: 50,
        borderRadius: 25,
        marginRight: 15,
    },
    content: {
        flex: 1,
        marginRight: 10,
    },
    rowBetween: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 4,
    },
    name: {
        fontSize: 15,
        fontWeight: 'bold',
        color: '#130160',
    },
    email: {
        fontSize: 13,
        color: '#524B6B',
        marginBottom: 2,
    },
    date: {
        fontSize: 11,
        color: '#AAA6B9',
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 8,
    },
    badgeText: {
        fontSize: 10,
        fontWeight: 'bold',
    },
});

export default JobApplicantsTab;