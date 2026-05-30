import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  TextInput,
  Platform,
} from 'react-native';

// Android emulator: 10.0.2.2 → host localhost. iOS simulator: localhost.
const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');

export default function App() {
  const [engineMode, setEngineMode] = useState('WESTERN');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [appData, setAppData] = useState(null);
  const [apiUrl, setApiUrl] = useState(API_BASE);

  const fetchChart = () => {
    setLoading(true);
    setError(null);
    fetch(`${apiUrl}/api/v1/chart/compute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        display_name: 'Production User',
        birth_date: '1995-08-15',
        birth_time: '14:30',
        latitude: 40.7128,
        longitude: -74.006,
        timezone_id: 'America/New_York',
        current_age: 28.5,
        persist: false,
      }),
    })
      .then((res) => {
        if (!res.ok) return res.json().then((j) => Promise.reject(j.detail || res.statusText));
        return res.json();
      })
      .then((json) => {
        setAppData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(String(err));
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchChart();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.hint}>Connecting to {apiUrl}</Text>
      </View>
    );
  }

  if (error || !appData) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorTitle}>Could not load chart</Text>
        <Text style={styles.errorText}>{error || 'Unknown error'}</Text>
        <TextInput
          style={styles.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          placeholder="API URL"
          placeholderTextColor="#64748B"
        />
        <TouchableOpacity style={styles.retryBtn} onPress={fetchChart}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const planets = appData.western?.planets || {};
  const aspects = appData.western?.aspects || [];
  const angles = appData.western?.houses?.angles || {};
  const vedicD1 = appData.vedic?.d1 || {};
  const vedicD9 = appData.vedic?.d9 || {};
  const acgSun = appData.astrocartography?.Sun?.vectors || [];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>COSMOCORE</Text>
        <Text style={styles.subtitle}>Swiss Ephemeris • Dual Engine</Text>
      </View>

      <View style={styles.tabRow}>
        {['WESTERN', 'VEDIC'].map((mode) => (
          <TouchableOpacity
            key={mode}
            style={[styles.tab, engineMode === mode && styles.activeTab]}
            onPress={() => setEngineMode(mode)}
          >
            <Text style={styles.tabText}>{mode}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.scroll}>
        {engineMode === 'WESTERN' && (
          <View style={styles.card}>
            <Text style={styles.cardTag}>Tropical planets</Text>
            {['Sun', 'Moon', 'Mercury', 'Venus', 'Mars'].map((p) =>
              planets[p] ? (
                <View key={p} style={styles.row}>
                  <Text style={styles.lbl}>{p}:</Text>
                  <Text style={styles.val}>
                    {planets[p].sign} {planets[p].degree}°
                    {planets[p].is_retrograde ? ' ℞' : ''}
                  </Text>
                </View>
              ) : null
            )}
            <Text style={[styles.cardTag, { marginTop: 15 }]}>Angles</Text>
            {angles.ASC && (
              <View style={styles.row}>
                <Text style={styles.lbl}>ASC:</Text>
                <Text style={styles.val}>
                  {angles.ASC.sign} {angles.ASC.degree}°
                </Text>
              </View>
            )}
            <Text style={[styles.cardTag, { marginTop: 15 }]}>Aspects</Text>
            {aspects.slice(0, 8).map((asp, idx) => (
              <Text key={idx} style={styles.aspectText}>
                {asp.p1} {asp.aspect} {asp.p2} (orb {asp.orb}°)
              </Text>
            ))}
          </View>
        )}

        {engineMode === 'VEDIC' && (
          <View style={styles.card}>
            <Text style={styles.cardTag}>
              Jyotish • Lahiri {appData.vedic?.ayanamsa}°
            </Text>
            {vedicD1.Sun && (
              <>
                <View style={styles.row}>
                  <Text style={styles.lbl}>Sun D-1:</Text>
                  <Text style={styles.val}>
                    {vedicD1.Sun.sign} • {vedicD1.Sun.nakshatra?.name} pada{' '}
                    {vedicD1.Sun.nakshatra?.pada}
                  </Text>
                </View>
                <View style={styles.row}>
                  <Text style={styles.lbl}>Sun D-9:</Text>
                  <Text style={styles.val}>{vedicD9.Sun?.sign}</Text>
                </View>
              </>
            )}
            {appData.vedic?.dashas?.current_mahadasha && (
              <View style={[styles.row, { marginTop: 10 }]}>
                <Text style={styles.lbl}>Mahadasha:</Text>
                <Text style={styles.val}>{appData.vedic.dashas.current_mahadasha}</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.timelineCard}>
          <Text style={styles.cardTag}>Firdaria</Text>
          <Text style={styles.heroText}>
            Major: {appData.firdaria?.major} • Sub: {appData.firdaria?.sub}
          </Text>
          <View style={styles.progressBar}>
            <View
              style={[styles.progressFill, { width: `${appData.firdaria?.progress || 0}%` }]}
            />
          </View>
        </View>

        <View style={styles.mapCard}>
          <Text style={styles.cardTag}>Astrocartography (Sun)</Text>
          {acgSun.slice(0, 4).map((vec, idx) => (
            <Text key={idx} style={styles.aspectText}>
              • h{vec.hour_meridian}: lat {vec.lat}, lon {vec.lon}
            </Text>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#05070F' },
  center: {
    flex: 1,
    backgroundColor: '#05070F',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  hint: { color: '#64748B', marginTop: 12 },
  header: { padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#FFF' },
  subtitle: { color: '#64748B', marginTop: 4, fontSize: 12 },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    marginHorizontal: 20,
    borderRadius: 8,
  },
  tab: { flex: 1, padding: 12, alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#4F46E5' },
  tabText: { color: '#FFF', fontWeight: 'bold' },
  scroll: { paddingHorizontal: 20, marginTop: 15 },
  card: { backgroundColor: '#0F172A', padding: 20, borderRadius: 12, marginBottom: 15 },
  timelineCard: {
    backgroundColor: '#312E81',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
  },
  mapCard: {
    backgroundColor: '#111827',
    padding: 20,
    borderRadius: 12,
    marginBottom: 30,
    borderWidth: 1,
    borderColor: '#1F2937',
  },
  cardTag: {
    color: '#818CF8',
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 4 },
  lbl: { color: '#94A3B8', flex: 1 },
  val: { color: '#FFF', fontWeight: 'bold', flex: 2, textAlign: 'right' },
  aspectText: { color: '#CBD5E1', marginTop: 4 },
  heroText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  progressBar: {
    height: 8,
    backgroundColor: '#1E293B',
    borderRadius: 4,
    marginTop: 10,
  },
  progressFill: { height: '100%', backgroundColor: '#818CF8', borderRadius: 4 },
  errorTitle: { color: '#F87171', fontSize: 18, fontWeight: 'bold' },
  errorText: { color: '#94A3B8', marginTop: 8, textAlign: 'center' },
  input: {
    marginTop: 16,
    width: '100%',
    backgroundColor: '#1E293B',
    color: '#FFF',
    padding: 12,
    borderRadius: 8,
  },
  retryBtn: {
    marginTop: 16,
    backgroundColor: '#4F46E5',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: { color: '#FFF', fontWeight: 'bold' },
});
