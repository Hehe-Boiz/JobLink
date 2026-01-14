import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, Image, TextInput, TouchableOpacity,
  Alert, KeyboardAvoidingView, Platform, Linking
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import styles from '../../styles/Employer/EmployerStyles';
import { authApis, endpoints } from '../../utils/Apis';
import { ActivityIndicator, Divider } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useDialog } from '../../hooks/useDialog';

const CandidateDetail = ({ route, navigation }) => {
  const application = route.params.application;


  const [comment, setComment] = useState('');
  const [rating, setRating] = useState(0);
  const [candidate, setCandidate] = useState({});
  const [loading, setLoading] = useState(true);
  const { showDialog } = useDialog();
 
  const load_candidate = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      console.log(application.candidate_id);
      setLoading(true);
      let res = await authApis(token).get(endpoints['candidate_by_applications_in_employer_jobs'](application.id));
      setCandidate(res.data);
    } catch (ex) {
      console.error(ex);
      Alert.alert("Lỗi", "Không tải được thông tin ứng viên.");
    } finally {
      setLoading(false);
    }
  }
  const comment_application = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('token');
      
      let res = await authApis(token).patch(endpoints['update_application'](application.id), {
        comment: comment,
        rating: rating
      });
      if (res.status === 200) {
        showDialog({
          title: "Thành Công!",
          content: "Đã lưu đánh giá ứng viên.",
          type: "success",
          buttonText: "TUYỆT VỜI",
          onPress: () => {
            console.log("Đã đóng dialog");
            navigation.goBack();
          }
        });
      }
    } catch (ex) {
      console.error(ex);
      showDialog({
        title: "Thất bại!",
        content: "Có lỗi xảy ra",
        type: "failed",
        buttonText: "ĐÓNG",
        onPress: () => {
          console.log("Đã đóng dialog");
          navigation.goBack();
        }
      });
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load_candidate();
  }, []);

 
  const handleViewCV = () => {
    const cvUrl = candidate?.cv_url || candidate?.resume;

    if (cvUrl) {
      Linking.openURL(cvUrl).catch(err => Alert.alert("Lỗi", "Không thể mở file CV."));
    } else {
      Alert.alert("Thông báo", "Ứng viên chưa cập nhật CV.");
    }
  };

  const handleSendComment = () => {
    if (rating === 0) {
      Alert.alert("Thông báo", "Vui lòng chọn số sao để đánh giá!");
      return;
    }
    
    console.log(application)
    console.log(comment);
    console.log(rating);
    comment_application();
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#130160" />
        <Text style={{ marginTop: 10, color: '#524B6B' }}>Đang tải hồ sơ...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F5F7FA' }} edges={['top', 'left', 'right']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <MaterialCommunityIcons name="arrow-left" size={24} color="#130160" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Hồ Sơ Ứng Viên</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>

          
          <View style={styles.profileCard}>
            <Image
              source={{ uri: "https://res.cloudinary.com/dblaqnihz/image/upload/v1767259778/lqtx6e6mymgyywf978v8.png" }}
              style={styles.profileAvatar}
            />

            <View style={{ alignItems: 'center', marginTop: 10 }}>
              <Text style={styles.profileName}>{candidate?.user?.last_name} {candidate?.user?.first_name}</Text>
              <Text style={styles.profileJob}>Ứng tuyển: {application?.job_title || "Developer"}</Text>

              {/* Status Badge */}
              <View style={[styles.statusBadge, { backgroundColor: '#E6E1FF', marginTop: 8 }]}>
                <Text style={{ color: '#2E5CFF', fontWeight: 'bold', fontSize: 12 }}>
                  {application?.status || "Chờ xét duyệt"}
                </Text>
              </View>
            </View>

            <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20, marginBottom: 10 }}>
              <IconInfo icon="email-outline" text="Email" onPress={() => Linking.openURL(`mailto:${candidate?.user?.email}`)} />
              <IconInfo icon="phone-outline" text="Gọi điện" onPress={() => Linking.openURL(`tel:${candidate?.phone || '0909000000'}`)} />
              <IconInfo icon="message-text-outline" text="Nhắn tin" />
            </View>
          </View>

          
          <Text style={styles.sectionHeader}>Thông tin cá nhân</Text>
          <View style={styles.infoCard}>
            <InfoItem icon="email" label="Email" value={candidate?.user?.email} />
            <Divider style={{ marginVertical: 10 }} />
            <InfoItem icon="phone" label="Điện thoại" value={candidate?.user?.phone || "Chưa cập nhật"} />
            <Divider style={{ marginVertical: 10 }} />
            <InfoItem icon="map-marker" label="Địa chỉ" value={candidate?.address || "Hồ Chí Minh, Việt Nam"} />
            <Divider style={{ marginVertical: 10 }} />
            <InfoItem icon="calendar" label="Ngày sinh" value={candidate?.dob || "01/01/1999"} />
          </View>

          
          <Text style={styles.sectionHeader}>Trình độ & Kinh nghiệm</Text>
          <View style={styles.infoCard}>
            {/* Học vấn */}
            <View style={{ flexDirection: 'row', marginBottom: 15 }}>
              <View style={styles.iconBox}>
                <MaterialCommunityIcons name="school-outline" size={24} color="#130160" />
              </View>
              <View style={{ marginLeft: 15, flex: 1 }}>
                <Text style={styles.infoLabel}>Học vấn</Text>
                <Text style={styles.infoValue}>{candidate?.school_name || "Đại học Bách Khoa TP.HCM"}</Text>
                <Text style={styles.infoSub}>{candidate?.education_status}</Text>
              </View>
            </View>

            <Divider style={{ marginBottom: 15 }} />

            
            <View style={{ flexDirection: 'row' }}>
              <View style={styles.iconBox}>
                <MaterialCommunityIcons name="briefcase-outline" size={24} color="#FF9228" />
              </View>
              <View style={{ marginLeft: 15, flex: 1 }}>
                <Text style={styles.infoLabel}>Kinh nghiệm</Text>
                <Text style={styles.infoValue}>{candidate?.experience || "3 Năm"}</Text>
                <Text style={styles.infoSub}>{candidate?.specialization}</Text>
              </View>
            </View>
          </View>

         
          <Text style={styles.sectionHeader}>Hồ sơ đính kèm</Text>
          <TouchableOpacity style={styles.cvCard} onPress={handleViewCV}>
            <View style={styles.cvIconContainer}>
              <MaterialCommunityIcons name="file-pdf-box" size={32} color="#FF4D4D" />
            </View>
            <View style={{ flex: 1, paddingHorizontal: 15 }}>
              <Text style={styles.cvName}>CV_{candidate?.user?.last_name || "UngVien"}.pdf</Text>
              <Text style={styles.cvSize}>Nhấn để xem chi tiết</Text>
            </View>
            <MaterialCommunityIcons name="eye" size={24} color="#AAA6B9" />
          </TouchableOpacity>

          
          <Text style={styles.sectionHeader}>Đánh giá & Ghi chú</Text>
          <View style={[styles.infoCard, { padding: 20 }]}>
            <View style={{ flexDirection: 'row', justifyContent: 'center', marginBottom: 20 }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <TouchableOpacity key={star} onPress={() => setRating(star)} style={{ marginHorizontal: 8 }}>
                  <MaterialCommunityIcons
                    name={star <= rating ? "star" : "star-outline"}
                    size={40}
                    color={star <= rating ? "#FF9228" : "#E0E0E0"}
                  />
                </TouchableOpacity>
              ))}
            </View>

            <TextInput
              style={styles.commentInputNew}
              placeholder="Ghi chú về ứng viên này..."
              multiline
              value={comment}
              onChangeText={setComment}
            />

            <TouchableOpacity style={styles.btnSave} onPress={handleSendComment}>
              <Text style={styles.btnSaveText}>LƯU ĐÁNH GIÁ</Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};


const IconInfo = ({ icon, text, onPress }) => (
  <TouchableOpacity onPress={onPress} style={{ alignItems: 'center' }}>
    <View style={{ width: 45, height: 45, borderRadius: 25, backgroundColor: '#F5F7FA', justifyContent: 'center', alignItems: 'center', marginBottom: 5 }}>
      <MaterialCommunityIcons name={icon} size={22} color="#524B6B" />
    </View>
    <Text style={{ fontSize: 12, color: '#524B6B' }}>{text}</Text>
  </TouchableOpacity>
);


const InfoItem = ({ icon, label, value }) => (
  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
    <MaterialCommunityIcons name={icon} size={20} color="#AAA6B9" style={{ width: 30 }} />
    <View>
      <Text style={{ fontSize: 12, color: '#95969D' }}>{label}</Text>
      <Text style={{ fontSize: 14, color: '#130160', fontWeight: '500', marginTop: 2 }}>{value}</Text>
    </View>
  </View>
);


export default CandidateDetail;