import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, TextInput, RefreshControl } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useIsFocused } from '@react-navigation/native';
import styles from '../../styles/Employer/EmployerStyles';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import JobCard from '../../components/Employer/JobCard'; 

const EmployerJobs = ({ navigation }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const isFocused = useIsFocused();

  const loadJobs = async () => {
    try {
        setLoading(true);
        const token = await AsyncStorage.getItem('token');
        const api = authApis(token);
        let res = await api.get(endpoints['employer_jobs']);
        setJobs(res.data.results || res.data);
    } catch (ex) {
        console.error(ex);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    if (isFocused) loadJobs();
  }, [isFocused]);


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

      {loading ? (
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
              <ActivityIndicator size="large" color="#130160" />
              <Text style={{ marginTop: 10, color: '#524B6B' }}>Đang tải dữ liệu...</Text>
          </View>
      ) : (
          <FlatList
            data={filteredJobs}
            keyExtractor={item => item.id.toString()}
            contentContainerStyle={{ padding: 20, paddingBottom: 80 }}
            refreshControl={<RefreshControl refreshing={loading} onRefresh={loadJobs} />}
            renderItem={({ item }) => (
                <JobCard 
                    job={item} 
                    onPress={() => navigation.navigate('JobApplicants', { job: item })}
                />
            )}
            ListEmptyComponent={
                <View style={{ alignItems: 'center', marginTop: 50 }}>
                    <MaterialCommunityIcons name="clipboard-text-off-outline" size={60} color="#DDD" />
                    <Text style={{ marginTop: 10, color: '#999' }}>Không tìm thấy tin nào.</Text>
                </View>
            }
          />
      )}
    </SafeAreaView>
  );
};

export default EmployerJobs;