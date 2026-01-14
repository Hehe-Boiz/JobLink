import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatCurrencyShort, formatDate, getJobStatus } from '../../utils/Helper';

const JobCard = ({ job, onPress, onEdit, onDelete }) => {
  const status = getJobStatus(job.deadline);

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.rowBetween}>
        <View style={{ flex: 1, marginRight: 10 }}>
          <Text style={styles.title} numberOfLines={1}>{job.title}</Text>
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


      <View style={styles.salaryContainer}>
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

          <View style={styles.statsContainer}>
            <MaterialCommunityIcons name="account-group" size={16} color="#130160" />
            <Text style={styles.statText}>12</Text>
          </View>

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

    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#F0F0F0',
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
    marginBottom: 4,
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
    borderTopColor: '#F5F5F5',
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
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E6E1FF', // Tím nhạt
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#130160',
    marginLeft: 4,
  },
  actionRow: {
      flexDirection: 'row',
      alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E6E1FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 10, // Cách nút sửa ra 1 chút
  },
  statText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#130160',
    marginLeft: 4,
  },
  iconBtn: {
      padding: 5,
      marginLeft: 5, // Khoảng cách giữa các nút
      backgroundColor: '#F5F7FA',
      borderRadius: 8,
  },
});

export default JobCard;