import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatCurrencyShort, formatDate, getJobStatus } from '../../utils/Helper';

const JobCard = ({ job, onPress, onEdit, onDelete, onBuyService }) => {
  const status = getJobStatus(job.deadline);

  const isFeatured = job.is_featured;

  return (
    <TouchableOpacity
      style={[styles.card, isFeatured && styles.featuredCard]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.rowBetween}>
        <View style={{ flex: 1, marginRight: 10 }}>

          <View>
            {isFeatured && (
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                <MaterialCommunityIcons name="star-four-points" size={12} color="#FF9228" />
                <Text style={{ fontSize: 10, fontWeight: 'bold', color: '#FF9228', marginLeft: 4 }}>
                  TIN NỔI BẬT
                </Text>
              </View>
            )}

            <View style={{ flexDirection: 'row', alignItems: 'center' }}>

              {isFeatured && (
                <MaterialCommunityIcons name="crown" size={20} color="#FF9228" style={{ marginRight: 6 }} />
              )}
              <Text
                style={[styles.title, isFeatured && { color: '#B36B00' }]} // Đổi màu chữ nếu VIP
                numberOfLines={1}
              >
                {job.title}
              </Text>
            </View>
          </View>


          <Text style={styles.idText}>ID: #{job.id}</Text>
        </View>

        <View style={[styles.badge, { backgroundColor: status.bg }]}>
          <Text style={[styles.badgeText, { color: status.color }]}>{status.label}</Text>
        </View>
      </View>

      <View style={styles.infoRow}>
        <View style={styles.infoItem}>
          <MaterialCommunityIcons name="map-marker-outline" size={16} color="#95969D" />
          <Text style={styles.infoText} numberOfLines={1}>
            {job.location_name || "Chưa cập nhật"}
          </Text>
        </View>
        <View style={[styles.infoItem, { marginLeft: 15 }]}>
          <MaterialCommunityIcons name="briefcase-outline" size={16} color="#95969D" />
          <Text style={styles.infoText}>
            {job.employment_type ? job.employment_type.replace('_', ' ') : 'Full-time'}
          </Text>
        </View>
      </View>

      <View style={[styles.salaryContainer, isFeatured && { backgroundColor: '#FFF' }]}>
        <Text style={styles.salaryLabel}>Mức lương:</Text>
        <Text style={styles.salaryValue}>
          {formatCurrencyShort(job.salary_min)} - {formatCurrencyShort(job.salary_max)} VNĐ
        </Text>
      </View>

      <View style={styles.footer}>
        <View style={styles.dateContainer}>
          <MaterialCommunityIcons name="clock-outline" size={14} color="#524B6B" />
          <Text style={styles.dateText}>Hạn: {formatDate(job.deadline)}</Text>
        </View>

        <View style={styles.actionRow}>
          {/* Nút Đẩy tin (Vẫn giữ để họ mua thêm gói gia hạn) */}
          <TouchableOpacity
            style={[styles.upgradeBtn, isFeatured && { backgroundColor: '#130160' }]} // Đổi màu nút nếu đã VIP
            onPress={onBuyService}
          >
            <MaterialCommunityIcons
              name={isFeatured ? "check-decagram" : "arrow-up-bold-circle"}
              size={16}
              color="#FFF"
            />
            <Text style={styles.upgradeText}>
              {isFeatured ? "Gia hạn" : "Đẩy tin"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.iconBtn} onPress={onEdit}>
            <MaterialCommunityIcons name="pencil-outline" size={20} color="#2E5CFF" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.iconBtn} onPress={onDelete}>
            <MaterialCommunityIcons name="trash-can-outline" size={20} color="#FF4D4D" />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 4,
  },
  
  featuredCard: {
    borderColor: '#FF9228', 
    borderWidth: 1.5,      
    backgroundColor: '#FFFBF0',
    
    shadowColor: "#FF9228",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 6,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#130160',
    marginBottom: 2,
    flex: 1
  },
  idText: {
    fontSize: 12,
    color: '#AAA6B9',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoText: {
    fontSize: 13,
    color: '#524B6B',
    marginLeft: 4,
  },
  salaryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    backgroundColor: '#F9F9F9',
    padding: 8,
    borderRadius: 8,
  },
  salaryLabel: {
    fontSize: 13,
    color: '#524B6B',
    marginRight: 5,
  },
  salaryValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#130160',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#eee', // Làm mờ viền footer một chút cho đẹp
    paddingTop: 12,
    marginTop: 5
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
    color: '#524B6B',
    marginLeft: 4,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBtn: {
    padding: 6,
    marginLeft: 8,
    backgroundColor: '#FFF', // Nền trắng để nổi trên nền vàng
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#EEE'
  },
  upgradeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF9228',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    marginRight: 4,
    shadowColor: "#FF9228",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  upgradeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#FFF',
    marginLeft: 4,
  },
});

export default JobCard;