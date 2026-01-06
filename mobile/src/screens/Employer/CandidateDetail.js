import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, Image, TextInput, TouchableOpacity, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons'; // Import Icon
import styles from '../../styles/Employer/EmployerStyles';
import {authApis, endpoints} from '../../utils/Apis';
const CandidateDetail = ({ route, navigation }) => {
  const application_id = route.params;
  const [comment, setComment] = useState('');
  const [rating, setRating] = useState(0);
  const [candidate, setCandidate] = useState({})
  const [loading, setLoading] = useState(true)
  const load_candidate = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      setLoading(true);
      let res = await authApis(token).get(endpoints['candidate_by_applications_in_employer_jobs'](application_id));
      setCandidate(res.data);
      console.log(candidate);
      setLoading(false);
    } catch (ex) {
      console.error(ex);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    console.log(candidate);
    load_candidate();
  }, []);

  const handleSendComment = () => {
    if (rating === 0) {
      Alert.alert("Thông báo", "Vui lòng chọn số sao để đánh giá ứng viên!");
      return;
    }
    Alert.alert("Đã lưu đánh giá", `⭐️ ${rating} sao\n📝 ${comment || "Không có"}`);
  };

  const renderStars = () => {
    return (
      <View style={{ flexDirection: 'row', justifyContent: 'center', marginBottom: 20 }}>
        {[1, 2, 3, 4, 5].map((star) => (
          <TouchableOpacity key={star} onPress={() => setRating(star)} style={{ marginHorizontal: 5 }}>
            <MaterialCommunityIcons
              name={star <= rating ? "star" : "star-outline"}
              size={36}
              color={star <= rating ? "#FF9228" : "#AAA6B9"}
            />
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: 'white' }]} edges={['top', 'left', 'right']}>

      {/* 2. BỌC KEYBOARD AVOIDING VIEW Ở ĐÂY */}
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === "ios" ? 10 : 0} // Tinh chỉnh khoảng cách nếu cần
      >
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }} // Thêm padding đáy để scroll được xuống hết
        >

          {/* 1. Header & Profile */}
          <View style={{ padding: 20 }}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={{ color: '#2E5CFF', marginBottom: 20 }}>← Quay lại danh sách</Text>
            </TouchableOpacity>

            <View style={{ alignItems: 'center', marginBottom: 20 }}>
              <Image source={{ uri: `https://randomuser.me/api/portraits/men/${candidate.id + 10}.jpg` }} style={{ width: 80, height: 80, borderRadius: 40, marginBottom: 10 }} />
              <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#130160' }}>{candidate.user.full_name}</Text>
              <Text style={{ color: '#524B6B' }}>Ứng tuyển: Senior Frontend Developer</Text>
            </View>

            <View style={{ backgroundColor: '#F9F9F9', padding: 15, borderRadius: 12 }}>
              <InfoRow label="Email" value={candidate.user.email} />
              <InfoRow label="Điện thoại" value="0912345678" />
              <InfoRow label="Ngày nộp" value="05/01/2026" />
              <InfoRow label="Trạng thái" value={candidate.status} isBadge bg={candidate.bg} color={candidate.statusColor} />
              <InfoRow label="Kinh nghiệm" value={candidate.exp} />
            </View>
          </View>

          {/* 2. KHUNG ĐÁNH GIÁ & BÌNH LUẬN */}
          <View style={styles.commentBox}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 10, textAlign: 'center' }}>
              Đánh giá hồ sơ
            </Text>

            <Text style={{ textAlign: 'center', color: '#524B6B', marginBottom: 10, fontSize: 13 }}>
              Chất lượng ứng viên này thế nào?
            </Text>

            {renderStars()}

            <Text style={{ fontSize: 14, fontWeight: '600', color: '#130160', marginBottom: 8 }}>
              Ghi chú nội bộ (Optional)
            </Text>
            <TextInput
              style={styles.commentInput}
              placeholder="Ví dụ: Ứng viên có kỹ năng tốt..."
              multiline
              value={comment}
              onChangeText={setComment}
            // Thêm dòng này để khi bấm Enter thì bàn phím tự ẩn (nếu muốn)
            // returnKeyType="done"
            // onSubmitEditing={() => Keyboard.dismiss()}
            />

            <TouchableOpacity style={styles.btnSend} onPress={handleSendComment}>
              <Text style={styles.btnText}>Lưu Đánh Giá</Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const InfoRow = ({ label, value, isBadge, bg, color }) => (
  <View style={{ marginBottom: 15 }}>
    <Text style={{ fontSize: 12, color: '#95969D' }}>{label}</Text>
    {isBadge ? (
      <View style={{ backgroundColor: bg, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, alignSelf: 'flex-start', marginTop: 4 }}>
        <Text style={{ color: color, fontWeight: 'bold', fontSize: 13 }}>{value}</Text>
      </View>
    ) : (
      <Text style={{ fontSize: 14, color: '#130160', marginTop: 2, fontWeight: '500' }}>{value}</Text>
    )}
  </View>
);

export default CandidateDetail;