import React from 'react';
import { View, Text, FlatList, TouchableOpacity, Image } from 'react-native';
import styles from '../../styles/Employer/EmployerStyles';
import { SafeAreaView } from 'react-native-safe-area-context';

const JobApplicants = ({ route, navigation }) => {
    const { job } = route.params || { job: { title: 'Unknown Job' } };

    const candidates = [
        { id: 1, name: 'Nguyễn Văn An', email: 'an.nguyen@email.com', exp: '3 năm kinh nghiệm React, Vue.js', status: 'Chờ xét duyệt', statusColor: '#FF9228', bg: '#FFF4E5' },
        { id: 2, name: 'Phạm Thị Dung', email: 'dung.pham@email.com', exp: '5 năm kinh nghiệm Frontend, Team Lead', status: 'Đã xem', statusColor: '#2E5CFF', bg: '#E6E1FF' },
    ];

    return (
        <View style={styles.container}>
            <SafeAreaView>
                <View style={{ padding: 20, backgroundColor: 'white', marginBottom: 10 }}>
                    <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginBottom: 10 }}>
                        <Text style={{ color: '#2E5CFF' }}>← Quay lại danh sách tin</Text>
                    </TouchableOpacity>
                    <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#130160' }}>{job.title}</Text>
                    <View style={styles.tagSuccess}>
                        <Text style={styles.tagTextSuccess}>Đang tuyển</Text>
                    </View>
                </View>
            </SafeAreaView>
            <View style={{ paddingHorizontal: 20, marginBottom: 10 }}>
                <Text style={{ fontSize: 16, fontWeight: 'bold' }}>Danh sách ứng viên ({candidates.length})</Text>
            </View>

            <FlatList
                data={candidates}
                keyExtractor={item => item.id.toString()}
                renderItem={({ item }) => (
                    <TouchableOpacity
                        style={styles.candidateItem}
                        onPress={() => navigation.navigate('CandidateDetail', { candidate: item })}
                    >
                        <Image source={{ uri: `https://randomuser.me/api/portraits/men/${item.id + 10}.jpg` }} style={styles.avatarLarge} />
                        <View style={{ flex: 1 }}>
                            <View style={styles.rowBetween}>
                                <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#130160' }}>{item.name}</Text>
                                <View style={[styles.statusBadge, { backgroundColor: item.bg }]}>
                                    <Text style={{ color: item.statusColor, fontSize: 12, fontWeight: 'bold' }}>{item.status}</Text>
                                </View>
                            </View>
                            <Text style={{ color: '#524B6B', fontSize: 13 }}>{item.email}</Text>
                            <Text style={{ color: '#95969D', fontSize: 12, marginTop: 4 }}>{item.exp}</Text>
                        </View>
                    </TouchableOpacity>
                )}
            />
        </View>
    );
};

export default JobApplicants;